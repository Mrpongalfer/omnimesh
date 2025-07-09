# OmniMesh Production Deployment Guide

## 🚀 Overview

This guide provides comprehensive instructions for deploying OmniMesh to production environments with enterprise-grade security, monitoring, and reliability features.

## 📋 Prerequisites

### System Requirements

- **Kubernetes**: v1.24+ with RBAC enabled
- **Docker**: v20.10+ with BuildKit support
- **Helm**: v3.8+ for package management
- **kubectl**: v1.24+ configured for your cluster
- **Node.js**: v18+ for frontend builds
- **Go**: v1.19+ for backend services
- **Rust**: v1.65+ for core components

### Security Requirements

- **TLS Certificates**: Valid SSL/TLS certificates for all domains
- **GPG Keys**: For package signing and verification
- **Secrets Management**: Kubernetes secrets or external secret management
- **Network Policies**: Firewall rules and network isolation
- **Monitoring**: Prometheus and Grafana for observability

### Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| Frontend (UI) | 100m-500m | 128Mi-512Mi | 1Gi |
| Backend (API) | 200m-1000m | 256Mi-1Gi | 2Gi |
| Core Services | 300m-1500m | 512Mi-2Gi | 5Gi |
| Monitoring | 500m-2000m | 1Gi-4Gi | 10Gi |
| **Total** | **1.1-5 CPU** | **2-8Gi RAM** | **18Gi** |

## 🔒 Security Hardening

### Pre-Deployment Security

1. **Run Security Audit**
   ```bash
   ./security-audit-complete.sh
   ```

2. **Update Dependencies**
   ```bash
   cd FRONTEND/ui-solidjs
   npm audit fix
   npm run security:deps
   ```

3. **Validate Configurations**
   ```bash
   ./scripts/pre-deployment-security-check.sh
   ```

### Network Security

- **Network Policies**: Implemented with default deny-all
- **Service Mesh**: Istio with mTLS enabled
- **Ingress**: NGINX with WAF protection
- **Firewall**: Cloud provider firewall rules

### Container Security

- **Base Images**: Distroless or minimal base images
- **Security Scanning**: Trivy vulnerability scanning
- **Non-Root**: All containers run as non-root users
- **Read-Only**: Root filesystems are read-only
- **Capabilities**: Dropped all unnecessary capabilities

## 🚀 Deployment Process

### 1. Environment Setup

```bash
# Clone repository
git clone https://github.com/Mrpongalfer/omnimesh.git OMNIMESH
cd OMNIMESH

# Set environment variables
export DEPLOYMENT_ENV=production
export NAMESPACE=omnimesh
export DOMAIN=omnimesh.local
export REGISTRY=ghcr.io/mrpongalfer/omnimesh
```

### 2. Pre-Deployment Checks

```bash
# Run pre-deployment security checks
./scripts/pre-deployment-security-check.sh

# Create deployment backup
./scripts/backup-production.sh

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### 3. Deploy Security Policies

```bash
# Apply security policies
kubectl apply -f kubernetes/security/

# Verify policies
kubectl get networkpolicies -n omnimesh
kubectl get podsecuritypolicies
```

### 4. Deploy Infrastructure

```bash
# Deploy monitoring stack
kubectl apply -f kubernetes/monitoring/

# Deploy logging stack
kubectl apply -f kubernetes/logging/

# Deploy storage classes
kubectl apply -f kubernetes/storage/
```

### 5. Deploy Applications

```bash
# Deploy with production script
./scripts/production-deploy.sh production

# OR deploy manually
kubectl apply -f kubernetes/applications/
```

### 6. Post-Deployment Validation

```bash
# Check deployment status
kubectl get pods -n omnimesh
kubectl get services -n omnimesh
kubectl get ingress -n omnimesh

# Run health checks
./scripts/health-check.sh

# Verify security posture
./scripts/security-posture-check.sh
```

## 🔧 Configuration Management

### Environment Variables

```yaml
# production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: omnimesh-config
  namespace: omnimesh
data:
  NODE_ENV: "production"
  LOG_LEVEL: "info"
  METRICS_ENABLED: "true"
  SECURITY_HEADERS: "true"
  CORS_ORIGINS: "https://omnimesh.local,https://app.omnimesh.local"
  API_RATE_LIMIT: "100"
  SESSION_TIMEOUT: "3600"
  JWT_EXPIRY: "1800"
```

### Secrets Management

```yaml
# production-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: omnimesh-secrets
  namespace: omnimesh
type: Opaque
data:
  JWT_SECRET: <base64-encoded-secret>
  DATABASE_URL: <base64-encoded-url>
  REDIS_PASSWORD: <base64-encoded-password>
  TLS_CERT: <base64-encoded-cert>
  TLS_KEY: <base64-encoded-key>
```

### TLS Configuration

```yaml
# tls-config.yaml
apiVersion: v1
kind: Secret
metadata:
  name: omnimesh-tls
  namespace: omnimesh
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-certificate>
  tls.key: <base64-encoded-private-key>
```

## 📊 Monitoring and Alerting

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'omnimesh-api'
    static_configs:
      - targets: ['omnimesh-api:8080']
    metrics_path: /metrics
    scrape_interval: 10s
```

### Grafana Dashboards

- **Application Metrics**: Response time, error rate, throughput
- **Infrastructure Metrics**: CPU, memory, disk, network
- **Security Metrics**: Failed logins, security violations
- **Business Metrics**: Active users, workflow executions

### Alert Rules

```yaml
# alert-rules.yaml
groups:
- name: omnimesh-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## 📝 Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# Daily backup script

# Backup Kubernetes resources
kubectl get all,configmaps,secrets,pvc -n omnimesh -o yaml > backup-$(date +%Y%m%d).yaml

# Backup persistent volumes
kubectl get pv -o yaml > pv-backup-$(date +%Y%m%d).yaml

# Backup to cloud storage
aws s3 cp backup-$(date +%Y%m%d).yaml s3://omnimesh-backups/
```

### Recovery Procedures

```bash
#!/bin/bash
# Recovery script

# Restore from backup
kubectl apply -f backup-$(date +%Y%m%d).yaml

# Verify recovery
kubectl get pods -n omnimesh
./scripts/health-check.sh
```

## 🔧 Troubleshooting

### Common Issues

1. **Pod Scheduling Issues**
   ```bash
   kubectl describe pod <pod-name> -n omnimesh
   kubectl get events -n omnimesh --sort-by=.metadata.creationTimestamp
   ```

2. **Network Connectivity**
   ```bash
   kubectl exec -it <pod-name> -n omnimesh -- nslookup kubernetes.default
   kubectl get networkpolicies -n omnimesh
   ```

3. **Resource Constraints**
   ```bash
   kubectl top pods -n omnimesh
   kubectl describe limitrange -n omnimesh
   ```

4. **Security Policy Violations**
   ```bash
   kubectl get events -n omnimesh | grep -i security
   kubectl describe podsecuritypolicy omnimesh-psp
   ```

### Log Analysis

```bash
# Application logs
kubectl logs -n omnimesh -l app=omnimesh-api --tail=100

# System logs
kubectl logs -n kube-system -l app=kube-proxy --tail=100

# Security logs
kubectl logs -n omnimesh -l app=security-monitor --tail=100
```

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update application
kubectl set image deployment/omnimesh-api omnimesh-api=ghcr.io/mrpongalfer/omnimesh/api:v2.0.0 -n omnimesh

# Monitor rollout
kubectl rollout status deployment/omnimesh-api -n omnimesh
```

### Security Updates

```bash
# Run security audit
./security-audit-complete.sh

# Update dependencies
cd FRONTEND/ui-solidjs
npm audit fix
npm run security:deps

# Redeploy with security patches
./scripts/production-deploy.sh production
```

### Maintenance Windows

- **Scheduled**: Monthly maintenance window (2nd Saturday, 2-6 AM UTC)
- **Emergency**: Security patches deployed within 24 hours
- **Regular**: Dependency updates every 2 weeks

## 📋 Compliance and Auditing

### SOC 2 Type II Compliance

- **Security**: Access controls, encryption, monitoring
- **Availability**: Uptime SLA, disaster recovery
- **Processing Integrity**: Data validation, workflow controls
- **Confidentiality**: Data classification, access logging
- **Privacy**: Data minimization, consent management

### Audit Logging

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
    
- level: Request
  resources:
  - group: ""
    resources: ["pods", "services"]
    
- level: Metadata
  resources:
  - group: ""
    resources: ["*"]
```

### Compliance Checks

```bash
# Run compliance scan
./scripts/compliance-check.sh

# Generate compliance report
./scripts/generate-compliance-report.sh
```

## 🎯 Performance Optimization

### Resource Optimization

```yaml
# production-resources.yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Horizontal Pod Autoscaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: omnimesh-hpa
  namespace: omnimesh
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: omnimesh-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 📞 Support and Escalation

### Support Channels

- **Level 1**: Documentation, FAQ, Community Forum
- **Level 2**: GitHub Issues, Email Support
- **Level 3**: Emergency Hotline, On-Call Engineering

### Emergency Procedures

1. **Incident Detection**: Automated alerts via Prometheus
2. **Initial Response**: On-call engineer responds within 15 minutes
3. **Escalation**: Severity 1 incidents escalated to leadership
4. **Communication**: Status page updates, customer notifications
5. **Resolution**: Root cause analysis, post-incident review

---

**Last Updated**: January 2025  
**Version**: 2.0.0-secure  
**Next Review**: February 2025
