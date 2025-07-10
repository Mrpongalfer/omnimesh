// nexus-prime-core/src/security.rs - Advanced Security and mTLS Implementation

use crate::config::SecurityConfig;
use rustls::{pki_types::{CertificateDer, PrivateKeyDer}, ServerConfig as RustlsServerConfig, ClientConfig as RustlsClientConfig};
use rustls_pemfile::{certs, pkcs8_private_keys};
use std::fs::File;
use std::io::BufReader;
use std::path::Path;
use std::sync::Arc;
use tonic::transport::{Identity, Certificate as TonicCertificate, ClientTlsConfig, ServerTlsConfig};
use uuid::Uuid;
use chrono::{DateTime, Utc, Duration};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tokio::sync::RwLock;

pub type SecurityResult<T> = Result<T, SecurityError>;

#[derive(Debug, thiserror::Error)]
pub enum SecurityError {
    #[error("TLS error: {0}")]
    Tls(#[from] rustls::Error),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Certificate error: {0}")]
    Certificate(String),
    #[error("Authentication failed: {0}")]
    Authentication(String),
    #[error("Authorization failed: {0}")]
    Authorization(String),
    #[error("Token error: {0}")]
    Token(String),
}

// Authentication token structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthToken {
    pub token_id: Uuid,
    pub entity_id: String,  // Node ID or user ID
    pub entity_type: EntityType,
    pub permissions: Vec<Permission>,
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EntityType {
    Node,
    User,
    Service,
    Agent,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Permission {
    // Node permissions
    RegisterNode,
    UpdateNodeStatus,
    DeployAgent,
    StopAgent,
    
    // Fabric management permissions
    ViewFabricStatus,
    ManageFabric,
    ViewTelemetry,
    ManageTelemetry,
    
    // Administrative permissions
    ManageUsers,
    ManageSecurityPolicy,
    ViewAuditLogs,
    
    // System permissions
    SystemControl,
    EmergencyAccess,
}

// Security manager for handling authentication, authorization, and TLS
pub struct SecurityManager {
    config: SecurityConfig,
    active_tokens: Arc<RwLock<HashMap<String, AuthToken>>>,
    revoked_tokens: Arc<RwLock<Vec<Uuid>>>,
}

impl SecurityManager {
    pub fn new(config: SecurityConfig) -> Self {
        Self {
            config,
            active_tokens: Arc::new(RwLock::new(HashMap::new())),
            revoked_tokens: Arc::new(RwLock::new(Vec::new())),
        }
    }

    // Create server TLS config for gRPC server
    pub fn create_server_tls_config(&self) -> SecurityResult<Option<ServerTlsConfig>> {
        if !self.config.enable_mtls {
            return Ok(None);
        }

        let cert_path = self.config.server_cert_path.as_ref()
            .ok_or_else(|| SecurityError::Certificate("Server certificate path not configured".to_string()))?;
        
        let key_path = self.config.server_key_path.as_ref()
            .ok_or_else(|| SecurityError::Certificate("Server key path not configured".to_string()))?;

        // Read certificate and key files
        let cert_pem = std::fs::read_to_string(cert_path)?;
        let key_pem = std::fs::read_to_string(key_path)?;

        let identity = Identity::from_pem(cert_pem.clone(), key_pem);

        let mut tls_config = ServerTlsConfig::new().identity(identity);

        // Configure client certificate verification if CA is provided
        if let Some(ca_cert_path) = &self.config.ca_cert_path {
            let ca_pem = std::fs::read_to_string(ca_cert_path)?;
            let ca_cert = TonicCertificate::from_pem(ca_pem);
            tls_config = tls_config.client_ca_root(ca_cert);
        }

        Ok(Some(tls_config))
    }

    // Create client TLS config for connecting to other services
    pub fn create_client_tls_config(&self, server_name: &str) -> SecurityResult<Option<ClientTlsConfig>> {
        if !self.config.enable_mtls {
            return Ok(None);
        }

        let mut tls_config = ClientTlsConfig::new().domain_name(server_name);

        // Add client certificate if available
        if let (Some(cert_path), Some(key_path)) = (&self.config.client_cert_path, &self.config.client_key_path) {
            let cert_pem = std::fs::read_to_string(cert_path)?;
            let key_pem = std::fs::read_to_string(key_path)?;
            let identity = Identity::from_pem(cert_pem, key_pem);
            tls_config = tls_config.identity(identity);
        }

        // Add CA certificate for server verification
        if let Some(ca_cert_path) = &self.config.ca_cert_path {
            let ca_pem = std::fs::read_to_string(ca_cert_path)?;
            let ca_cert = TonicCertificate::from_pem(ca_pem);
            tls_config = tls_config.ca_certificate(ca_cert);
        }

        Ok(Some(tls_config))
    }

    // Generate authentication token
    pub async fn generate_token(&self, entity_id: String, entity_type: EntityType, permissions: Vec<Permission>) -> SecurityResult<String> {
        let token = AuthToken {
            token_id: Uuid::new_v4(),
            entity_id: entity_id.clone(),
            entity_type,
            permissions,
            issued_at: Utc::now(),
            expires_at: Utc::now() + Duration::minutes(self.config.session_timeout_minutes as i64),
            metadata: HashMap::new(),
        };

        let token_string = self.encode_token(&token)?;
        
        // Store active token
        let mut active_tokens = self.active_tokens.write().await;
        active_tokens.insert(token_string.clone(), token);

        Ok(token_string)
    }

    // Validate authentication token
    pub async fn validate_token(&self, token_string: &str) -> SecurityResult<AuthToken> {
        // Check if token is revoked
        let revoked_tokens = self.revoked_tokens.read().await;
        
        let active_tokens = self.active_tokens.read().await;
        let token = active_tokens.get(token_string)
            .ok_or_else(|| SecurityError::Authentication("Token not found".to_string()))?;

        // Check if token is revoked
        if revoked_tokens.contains(&token.token_id) {
            return Err(SecurityError::Authentication("Token has been revoked".to_string()));
        }

        // Check if token is expired
        if Utc::now() > token.expires_at {
            return Err(SecurityError::Authentication("Token has expired".to_string()));
        }

        Ok(token.clone())
    }

    // Check if entity has specific permission
    pub async fn check_permission(&self, token_string: &str, required_permission: &Permission) -> SecurityResult<bool> {
        let token = self.validate_token(token_string).await?;
        Ok(token.permissions.contains(required_permission))
    }

    // Revoke authentication token
    pub async fn revoke_token(&self, token_string: &str) -> SecurityResult<()> {
        let mut active_tokens = self.active_tokens.write().await;
        
        if let Some(token) = active_tokens.remove(token_string) {
            let mut revoked_tokens = self.revoked_tokens.write().await;
            revoked_tokens.push(token.token_id);
        }

        Ok(())
    }

    // Clean up expired tokens
    pub async fn cleanup_expired_tokens(&self) -> SecurityResult<usize> {
        let mut active_tokens = self.active_tokens.write().await;
        let now = Utc::now();
        
        let mut expired_count = 0;
        active_tokens.retain(|_, token| {
            if now > token.expires_at {
                expired_count += 1;
                false
            } else {
                true
            }
        });

        log::info!("Cleaned up {} expired authentication tokens", expired_count);
        Ok(expired_count)
    }

    // Audit logging for security events
    pub async fn log_security_event(&self, event_type: &str, entity_id: &str, details: HashMap<String, String>) {
        let event = SecurityAuditEvent {
            timestamp: Utc::now(),
            event_type: event_type.to_string(),
            entity_id: entity_id.to_string(),
            details,
        };

        // Log to system logs
        log::warn!("SECURITY_EVENT: {:?}", event);
        
        // In production, this would also write to a dedicated audit log storage
        // and potentially trigger alerts for suspicious activities
    }

    // Encode token (simplified - in production, use proper JWT or similar)
    fn encode_token(&self, token: &AuthToken) -> SecurityResult<String> {
        let serialized = serde_json::to_string(token)
            .map_err(|e| SecurityError::Token(format!("Failed to serialize token: {}", e)))?;
        
        // In production, this should use proper HMAC signing with the secret key
        let encoded = base64::encode(serialized);
        Ok(format!("{}:{}", self.config.auth_token_secret, encoded))
    }

    // Start background cleanup task
    pub fn start_cleanup_task(&self) -> tokio::task::JoinHandle<()> {
        let security_manager = self.clone();
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(300)); // 5 minutes
            
            loop {
                interval.tick().await;
                
                if let Err(e) = security_manager.cleanup_expired_tokens().await {
                    log::error!("Failed to cleanup expired tokens: {}", e);
                }
            }
        })
    }
}

impl Clone for SecurityManager {
    fn clone(&self) -> Self {
        Self {
            config: self.config.clone(),
            active_tokens: Arc::clone(&self.active_tokens),
            revoked_tokens: Arc::clone(&self.revoked_tokens),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct SecurityAuditEvent {
    timestamp: DateTime<Utc>,
    event_type: String,
    entity_id: String,
    details: HashMap<String, String>,
}

// Helper functions for certificate management
pub fn load_certificates(path: &Path) -> SecurityResult<Vec<Certificate>> {
    let certfile = File::open(path)?;
    let mut reader = BufReader::new(certfile);
    let certs = certs(&mut reader)?
        .into_iter()
        .map(Certificate)
        .collect();
    Ok(certs)
}

pub fn load_private_key(path: &Path) -> SecurityResult<PrivateKey> {
    let keyfile = File::open(path)?;
    let mut reader = BufReader::new(keyfile);
    let keys = pkcs8_private_keys(&mut reader)?;
    
    if keys.is_empty() {
        return Err(SecurityError::Certificate("No private key found".to_string()));
    }
    
    Ok(PrivateKey(keys[0].clone()))
}

// Certificate generation utilities (for development/testing)
#[cfg(feature = "cert-generation")]
pub mod cert_generation {
    use super::*;
    use rcgen::{Certificate as RcgenCertificate, CertificateParams, DistinguishedName};
    use std::fs;

    pub fn generate_self_signed_cert(common_name: &str, output_dir: &Path) -> SecurityResult<()> {
        let mut params = CertificateParams::new(vec![common_name.to_string()]);
        params.distinguished_name = DistinguishedName::new();
        params.distinguished_name.push(rcgen::DnType::CommonName, common_name);
        params.distinguished_name.push(rcgen::DnType::OrganizationName, "Omnitide Compute Fabric");
        
        let cert = RcgenCertificate::from_params(params)
            .map_err(|e| SecurityError::Certificate(format!("Failed to generate certificate: {}", e)))?;
        
        // Write certificate and key files
        let cert_pem = cert.serialize_pem()
            .map_err(|e| SecurityError::Certificate(format!("Failed to serialize certificate: {}", e)))?;
        let key_pem = cert.serialize_private_key_pem();
        
        fs::write(output_dir.join("cert.pem"), cert_pem)?;
        fs::write(output_dir.join("key.pem"), key_pem)?;
        
        Ok(())
    }
}
