# 🚨 CRITICAL FAILURE PROCEDURES - OmniMesh Operational Runbooks

**Classification:** RESTRICTED - OPERATIONS ONLY  
**Version:** 1.0.0  
**Last Updated:** July 7, 2025  
**Authority:** Tiger Lily Compliance Framework  

---

## ⚠️ IMMEDIATE ESCALATION MATRIX

| **Severity** | **Response Time** | **Primary Contact** | **Escalation** |
|-------------|-------------------|-------------------|----------------|
| **CRITICAL** | 5 minutes | SRE On-Call | VP Engineering |
| **HIGH** | 15 minutes | Platform Team | Engineering Manager |
| **MEDIUM** | 1 hour | Dev Team | Team Lead |
| **LOW** | 24 hours | Developer | Self-Service |

### 📞 Emergency Contact Chain
1. **SRE On-Call:** `+1-555-SRE-CALL` (Primary)
2. **Platform Team:** `+1-555-PLATFORM` (Secondary)
3. **Engineering Manager:** `+1-555-ENG-MGR` (Escalation)
4. **VP Engineering:** `+1-555-VP-ENG` (Executive)

---

## 🔥 RUNBOOK 1: CrashLoopBackoff Recovery

### Symptoms
- Pod restart count > 5 in 10 minutes
- Application logs show repeated startup failures
- Health check endpoints returning 500/503
- Memory/CPU usage spikes before crash

### Immediate Actions (0-5 minutes)
```bash
# 1. Check pod status and logs
kubectl get pods -n omnimesh-core -l app=nexus-prime-core
kubectl logs -n omnimesh-core -l app=nexus-prime-core --previous --tail=100

# 2. Check resource constraints
kubectl describe pod -n omnimesh-core <pod-name>
kubectl top pods -n omnimesh-core

# 3. Check events for scheduling issues
kubectl get events -n omnimesh-core --sort-by=.metadata.creationTimestamp
```

### Root Cause Analysis (5-15 minutes)
1. **Resource Exhaustion:** Check memory limits, CPU limits, storage
2. **Configuration Issues:** Validate ConfigMaps, Secrets, environment variables
3. **Dependencies:** Verify database connectivity, external service availability
4. **Code Issues:** Review recent deployments, check error logs

### Recovery Actions
```bash
# Emergency resource scaling
kubectl scale deployment nexus-prime-core --replicas=3 -n omnimesh-core

# Restart with resource increase
kubectl patch deployment nexus-prime-core -n omnimesh-core -p '{"spec":{"template":{"spec":{"containers":[{"name":"nexus-prime-core","resources":{"requests":{"memory":"2Gi","cpu":"1000m"},"limits":{"memory":"4Gi","cpu":"2000m"}}}]}}}}'

# Rollback to previous version if needed
kubectl rollout undo deployment/nexus-prime-core -n omnimesh-core
```

### Post-Recovery Checklist
- [ ] Verify all services are healthy
- [ ] Check metrics and alerting
- [ ] Document root cause
- [ ] Schedule post-mortem
- [ ] Update resource limits if needed

---

## 🗄️ RUNBOOK 2: Database Failure Recovery

### Symptoms
- Connection timeouts to PostgreSQL/RocksDB
- Database connection pool exhaustion
- Persistent storage issues
- Data corruption warnings

### Immediate Actions (0-5 minutes)
```bash
# 1. Check database pod status
kubectl get pods -n omnimesh-data -l app=postgresql
kubectl get pvc -n omnimesh-data

# 2. Check database logs
kubectl logs -n omnimesh-data -l app=postgresql --tail=100

# 3. Verify storage health
kubectl get pv
df -h /var/lib/postgresql/data
```

### Critical Database Commands
```bash
# Check PostgreSQL status
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT version();"

# Check connection count
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check database locks
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT * FROM pg_locks WHERE granted = false;"
```

### Recovery Actions
```bash
# Emergency read-only mode
kubectl patch configmap postgres-config -n omnimesh-data --patch '{"data":{"postgresql.conf":"default_transaction_read_only = on"}}'

# Restart PostgreSQL
kubectl delete pod postgresql-0 -n omnimesh-data

# Restore from backup (if needed)
kubectl exec -it postgresql-0 -n omnimesh-data -- pg_restore -U postgres -d omnimesh_db /backups/latest.dump
```

### Database Health Verification
```bash
# Verify database integrity
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT pg_database_size('omnimesh_db');"

# Check replication lag (if applicable)
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT * FROM pg_stat_replication;"
```

---

## 🌐 RUNBOOK 3: Network Partition Recovery

### Symptoms
- Inter-service communication failures
- gRPC connection timeouts
- Service mesh routing issues
- DNS resolution failures

### Immediate Actions (0-5 minutes)
```bash
# 1. Check network connectivity
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- ping google.com
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- nslookup kubernetes.default.svc.cluster.local

# 2. Check service mesh status
kubectl get pods -n istio-system
kubectl get destinationrules -n omnimesh-core
kubectl get virtualservices -n omnimesh-core
```

### Network Diagnostics
```bash
# Check pod-to-pod connectivity
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- nc -zv go-node-proxy-service 8080

# Check DNS resolution
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- dig +short kubernetes.default.svc.cluster.local

# Check iptables rules
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- iptables -L -n
```

### Recovery Actions
```bash
# Restart networking components
kubectl delete pod -n kube-system -l k8s-app=kube-dns
kubectl delete pod -n istio-system -l app=istio-proxy

# Reset service mesh configuration
kubectl delete destinationrule --all -n omnimesh-core
kubectl delete virtualservice --all -n omnimesh-core
kubectl apply -f k8s/service-mesh/
```

---

## 🧠 RUNBOOK 4: Memory Leak Mitigation

### Symptoms
- Gradual memory usage increase
- OOMKilled containers
- Performance degradation
- GC pressure warnings

### Immediate Actions (0-5 minutes)
```bash
# 1. Check memory usage
kubectl top pods -n omnimesh-core --sort-by=memory
kubectl describe pod -n omnimesh-core <pod-name> | grep -A5 -B5 "memory"

# 2. Generate memory dumps
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- kill -USR1 1

# 3. Check application metrics
curl -s http://nexus-prime-core-metrics:8080/metrics | grep memory
```

### Memory Analysis
```bash
# Check heap usage (if applicable)
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- cat /proc/meminfo

# Monitor memory allocation patterns
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- top -o %MEM

# Check for memory leaks in logs
kubectl logs -n omnimesh-core -l app=nexus-prime-core | grep -i "memory\|heap\|gc\|oom"
```

### Recovery Actions
```bash
# Immediate memory relief
kubectl patch deployment nexus-prime-core -n omnimesh-core -p '{"spec":{"template":{"spec":{"containers":[{"name":"nexus-prime-core","resources":{"limits":{"memory":"8Gi"}}}]}}}}'

# Rolling restart with memory monitoring
kubectl rollout restart deployment/nexus-prime-core -n omnimesh-core
kubectl rollout status deployment/nexus-prime-core -n omnimesh-core
```

---

## 🔐 RUNBOOK 5: Certificate Expiration Emergency

### Symptoms
- TLS handshake failures
- Certificate validation errors
- Service mesh mTLS failures
- External API authentication failures

### Immediate Actions (0-5 minutes)
```bash
# 1. Check certificate expiration
kubectl get secrets -n omnimesh-core -o jsonpath='{.items[*].metadata.name}' | xargs -I {} kubectl get secret {} -n omnimesh-core -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates

# 2. Check service mesh certificates
kubectl get secret -n istio-system cacerts -o jsonpath='{.data.cert-chain\.pem}' | base64 -d | openssl x509 -noout -dates
```

### Certificate Renewal
```bash
# Emergency certificate renewal
kubectl delete secret tls-secret -n omnimesh-core
kubectl create secret tls tls-secret -n omnimesh-core --cert=path/to/new/cert.pem --key=path/to/new/key.pem

# Restart affected services
kubectl rollout restart deployment/nexus-prime-core -n omnimesh-core
kubectl rollout restart deployment/go-node-proxy -n omnimesh-core
```

### Certificate Health Check
```bash
# Verify certificate installation
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- openssl s_client -connect localhost:8443 -servername nexus-prime-core

# Check certificate chain
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- openssl x509 -in /etc/tls/tls.crt -text -noout
```

---

## 🔄 RUNBOOK 6: Rollback Procedures

### Immediate Rollback Commands
```bash
# Application rollback
kubectl rollout undo deployment/nexus-prime-core -n omnimesh-core
kubectl rollout status deployment/nexus-prime-core -n omnimesh-core

# Database rollback (if schema changes)
kubectl exec -it postgresql-0 -n omnimesh-data -- pg_restore -U postgres -d omnimesh_db /backups/pre-deployment.dump

# Configuration rollback
kubectl apply -f k8s/configs/previous-version/
```

### Rollback Verification
```bash
# Verify application version
kubectl get deployment nexus-prime-core -n omnimesh-core -o jsonpath='{.spec.template.spec.containers[0].image}'

# Check health endpoints
curl -f http://nexus-prime-core-service:8080/health

# Verify database integrity
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT version();"
```

---

## 📊 RUNBOOK 7: Performance Degradation Response

### Symptoms
- Response time > 2 seconds
- Throughput drop > 50%
- CPU/Memory usage > 80%
- Error rate > 5%

### Immediate Actions (0-5 minutes)
```bash
# 1. Check system metrics
kubectl top pods -n omnimesh-core
kubectl top nodes

# 2. Check application performance
curl -s http://nexus-prime-core-metrics:8080/metrics | grep -E "(response_time|throughput|error_rate)"

# 3. Scale up immediately
kubectl scale deployment nexus-prime-core --replicas=5 -n omnimesh-core
```

### Performance Analysis
```bash
# Check resource utilization
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- cat /proc/loadavg
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- iostat -x 1 5

# Analyze application bottlenecks
kubectl logs -n omnimesh-core -l app=nexus-prime-core | grep -i "slow\|timeout\|bottleneck"
```

### Performance Recovery
```bash
# Horizontal scaling
kubectl patch hpa nexus-prime-core -n omnimesh-core -p '{"spec":{"maxReplicas":10}}'

# Vertical scaling
kubectl patch deployment nexus-prime-core -n omnimesh-core -p '{"spec":{"template":{"spec":{"containers":[{"name":"nexus-prime-core","resources":{"requests":{"cpu":"2000m","memory":"4Gi"},"limits":{"cpu":"4000m","memory":"8Gi"}}}]}}}}'
```

---

## 🚨 ESCALATION PROCEDURES

### Critical Escalation (0-5 minutes)
1. **Page SRE On-Call:** Automated via PagerDuty
2. **Create Incident:** JIRA High Priority ticket
3. **Notify Leadership:** Auto-escalation after 10 minutes
4. **Activate War Room:** Confluence incident page

### Communication Template
```
SUBJECT: [CRITICAL] OmniMesh Production Incident - [BRIEF DESCRIPTION]

STATUS: ACTIVE
IMPACT: [USER IMPACT DESCRIPTION]
AFFECTED SERVICES: [SERVICE LIST]
STARTED: [TIMESTAMP]
RESPONDERS: [TEAM MEMBERS]

CURRENT ACTIONS:
- [ACTION 1]
- [ACTION 2]

NEXT UPDATE: [TIMESTAMP]
```

### Incident Commands
```bash
# Create incident tracking
kubectl create configmap incident-tracker --from-literal=incident_id=$(date +%s) --from-literal=severity=critical --from-literal=status=active -n omnimesh-core

# Enable debug logging
kubectl patch configmap app-config -n omnimesh-core --patch '{"data":{"log_level":"debug"}}'

# Collect diagnostic data
kubectl cluster-info dump --output-directory=/tmp/incident-$(date +%s)
```

---

## 🔍 DIAGNOSTIC COMMANDS

### System Health Check
```bash
#!/bin/bash
# health_check.sh - Comprehensive system health verification

echo "=== OmniMesh Health Check ==="
echo "Timestamp: $(date)"
echo "Kubernetes Cluster:"
kubectl cluster-info

echo "=== Pod Status ==="
kubectl get pods -n omnimesh-core -o wide

echo "=== Service Status ==="
kubectl get svc -n omnimesh-core

echo "=== Resource Usage ==="
kubectl top pods -n omnimesh-core
kubectl top nodes

echo "=== Application Health ==="
curl -s http://nexus-prime-core-service:8080/health | jq .

echo "=== Database Health ==="
kubectl exec -it postgresql-0 -n omnimesh-data -- psql -U postgres -c "SELECT 1;"

echo "=== Network Connectivity ==="
kubectl exec -it nexus-prime-core-0 -n omnimesh-core -- ping -c 3 google.com

echo "=== Certificate Status ==="
kubectl get secrets -n omnimesh-core | grep tls

echo "=== Recent Events ==="
kubectl get events -n omnimesh-core --sort-by=.metadata.creationTimestamp | tail -10
```

### Log Collection
```bash
#!/bin/bash
# collect_logs.sh - Comprehensive log collection

INCIDENT_ID=$(date +%s)
LOG_DIR="/tmp/omnimesh-logs-$INCIDENT_ID"
mkdir -p $LOG_DIR

echo "Collecting logs for incident: $INCIDENT_ID"

# Application logs
kubectl logs -n omnimesh-core -l app=nexus-prime-core --previous > $LOG_DIR/nexus-prime-core-previous.log
kubectl logs -n omnimesh-core -l app=nexus-prime-core > $LOG_DIR/nexus-prime-core-current.log

# Database logs
kubectl logs -n omnimesh-data -l app=postgresql > $LOG_DIR/postgresql.log

# System logs
kubectl logs -n kube-system -l k8s-app=kube-dns > $LOG_DIR/kube-dns.log

# Events
kubectl get events -n omnimesh-core --sort-by=.metadata.creationTimestamp > $LOG_DIR/events.log

# Metrics
curl -s http://nexus-prime-core-metrics:8080/metrics > $LOG_DIR/metrics.txt

echo "Logs collected in: $LOG_DIR"
tar -czf omnimesh-logs-$INCIDENT_ID.tar.gz $LOG_DIR
```

---

## 📋 POST-INCIDENT PROCEDURES

### Immediate Post-Recovery (0-30 minutes)
1. **Verify System Health:** Run full health check
2. **Document Timeline:** Record all actions taken
3. **Collect Artifacts:** Save logs, metrics, configurations
4. **Notify Stakeholders:** Update incident status
5. **Schedule Post-Mortem:** Within 24 hours

### Post-Mortem Template
```markdown
# Post-Mortem: [INCIDENT TITLE]

## Incident Summary
- **Date:** [DATE]
- **Duration:** [DURATION]
- **Impact:** [IMPACT DESCRIPTION]
- **Root Cause:** [ROOT CAUSE]

## Timeline
- [TIMESTAMP] - [EVENT]
- [TIMESTAMP] - [EVENT]

## Root Cause Analysis
### What Happened
[DETAILED DESCRIPTION]

### Why It Happened
[ROOT CAUSE ANALYSIS]

### Contributing Factors
- [FACTOR 1]
- [FACTOR 2]

## Action Items
- [ ] [ACTION ITEM 1] - [OWNER] - [DUE DATE]
- [ ] [ACTION ITEM 2] - [OWNER] - [DUE DATE]

## Lessons Learned
- [LESSON 1]
- [LESSON 2]
```

### Preventive Measures
1. **Update Monitoring:** Add new alerts based on incident
2. **Improve Documentation:** Update runbooks with new procedures
3. **Enhance Testing:** Add chaos engineering scenarios
4. **Train Team:** Conduct incident response training
5. **Review Architecture:** Identify single points of failure

---

## 🎯 SUCCESS METRICS

### Recovery Time Objectives (RTO)
- **Critical Issues:** < 15 minutes
- **High Priority:** < 1 hour
- **Medium Priority:** < 4 hours
- **Low Priority:** < 24 hours

### Recovery Point Objectives (RPO)
- **Database:** < 1 hour data loss
- **Configuration:** < 5 minutes
- **Application State:** < 15 minutes

### Operational Metrics
- **Mean Time to Detection (MTTD):** < 2 minutes
- **Mean Time to Resolution (MTTR):** < 30 minutes
- **Incident Response Time:** < 5 minutes
- **False Positive Rate:** < 5%

### Monitoring Dashboards
- **Grafana:** `https://grafana.omnimesh.internal/d/incident-response`
- **Prometheus:** `https://prometheus.omnimesh.internal/graph`
- **Jaeger:** `https://jaeger.omnimesh.internal/search`
- **ELK:** `https://kibana.omnimesh.internal/app/logs`

---

## 📚 REFERENCE DOCUMENTATION

### Internal Documentation
- [OmniMesh Architecture Guide](../architecture/README.md)
- [Deployment Procedures](../deployment/README.md)
- [Monitoring Setup](../monitoring/README.md)
- [Security Procedures](../security/README.md)

### External References
- [Kubernetes Troubleshooting](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Istio Debugging](https://istio.io/latest/docs/ops/common-problems/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/current/admin.html)
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/)

---

**⚠️ IMPORTANT:** This runbook is classified as RESTRICTED. Only authorized personnel should have access. All actions taken using these procedures must be logged and audited.

**Last Review:** July 7, 2025  
**Next Review:** October 7, 2025  
**Document Owner:** SRE Team  
**Approved By:** Tiger Lily Compliance Officer
