# Istio E2E Encryption Configuration Guide

This guide will help you configure Istio for complete E2E encryption, including HTTPS termination at the ingress gateway and strict mTLS between services.

## **Important Architecture Clarification:**

You have **Istio Ingress Gateway** already installed. This chart does **NOT** install another gateway. Instead, it:

1. **Creates a TLS certificate** for your existing Istio Ingress Gateway
2. **Configures a Gateway resource** that tells your existing Istio Ingress Gateway how to handle traffic
3. **Sets up routing rules** (VirtualService) for your applications
4. **Enables mTLS** between services

### **Architecture Flow:**
```
Web Browser → HTTPS → [Existing Istio Ingress Gateway] → Frontend App → Backend App
                            ↑                              ↑           ↑
                      Certificate +                   mTLS here   mTLS here
                      Gateway config
```

## Prerequisites

- K3D cluster with Istio installed
- cert-manager and cert-manager-config already deployed
- Frontend and backend applications deployed in `my-demo` namespace
- Applications should have Istio sidecar injection enabled

## Step 1: Verify Prerequisites

```bash
# Check Istio installation
kubectl get pods -n istio-system

# Check cert-manager is working
kubectl get certificate -n cert-manager

# Check your applications are running
kubectl get pods -n my-demo

# Verify Istio sidecar injection is enabled for my-demo namespace
kubectl get namespace my-demo -o yaml | grep istio-injection
```

If sidecar injection is not enabled:
```bash
kubectl label namespace my-demo istio-injection=enabled
# Restart your application pods to get sidecars injected
kubectl rollout restart deployment -n my-demo
```

## Step 2: Deploy Istio E2E Encryption Configuration

Deploy the encryption configuration chart:

```bash
# Install the istio-encryption-config chart
helm install istio-encryption-config ./helm-charts/istio-encryption-config \
  --namespace istio-system \
  --wait

# Check installation status
helm status istio-encryption-config --namespace istio-system
```

## Step 3: Verify TLS Certificate

```bash
# Check if the TLS certificate was created and is ready
kubectl get certificate demo-app-tls -n istio-system
kubectl describe certificate demo-app-tls -n istio-system

# Check the certificate secret
kubectl get secret demo-app-tls-secret -n istio-system

# Wait for certificate to be ready (if needed)
kubectl wait --for=condition=ready certificate demo-app-tls -n istio-system --timeout=300s
```

## Step 4: Verify Istio Resources

```bash
# Check Gateway
kubectl get gateway demo-app-gateway -n istio-system
kubectl describe gateway demo-app-gateway -n istio-system

# Check VirtualService
kubectl get virtualservice demo-app-vs -n my-demo
kubectl describe virtualservice demo-app-vs -n my-demo

# Check DestinationRules
kubectl get destinationrule -n my-demo

# Check PeerAuthentication (strict mTLS)
kubectl get peerauthentication -n my-demo
```

## Step 5: Get External Access Information

```bash
# Get the ingress gateway external IP/port
kubectl get svc istio-ingressgateway -n istio-system

# For K3D, you might need to use port-forwarding or LoadBalancer setup
# Check your K3D cluster configuration for external access
```

## Step 6: Test HTTPS Access

### Option A: Direct Testing (if you have external IP)

```bash
# Test HTTP redirect to HTTPS
curl -v http://demo-app.127.0.0.1.nip.io

# Test HTTPS access (use -k for self-signed cert)
curl -k -v https://demo-app.127.0.0.1.nip.io

# Test backend API
curl -k -v https://demo-app.127.0.0.1.nip.io/api/health
```

### Option B: Port Forward Testing (for K3D)

```bash
# Port forward the istio-ingressgateway
kubectl port-forward -n istio-system svc/istio-ingressgateway 8443:443 8080:80

# Test in another terminal
curl -k -v https://demo-app.127.0.0.1.nip.io:8443
curl -k -v https://demo-app.127.0.0.1.nip.io:8443/api/health
```

### Option C: Browser Testing

1. Add port-forward: `kubectl port-forward -n istio-system svc/istio-ingressgateway 8443:443`
2. Visit: `https://demo-app.127.0.0.1.nip.io:8443`
3. Accept the self-signed certificate warning
4. Verify both frontend and backend (/api/) routes work

## Step 7: Verify E2E Encryption

Check that strict mTLS is working between services:

```bash
# Check mTLS status
istioctl authn tls-check -n my-demo

# Check proxy configuration
istioctl proxy-config cluster -n my-demo <frontend-pod-name>

# Check certificates in sidecars
istioctl proxy-config secret -n my-demo <frontend-pod-name>
```

## Configuration Customization

You can customize the setup by creating a custom values file:

```yaml
# custom-gateway-values.yaml
domain:
  name: my-custom-domain.127.0.0.1.nip.io
  aliases:
    - alt-domain.127.0.0.1.nip.io

virtualService:
  http:
    backend:
      match:
        - uri:
            prefix: /api/v1/
        - uri:
            prefix: /health
```

Then install with custom values:
```bash
helm install istio-gateway ./helm-charts/istio-gateway \
  --namespace istio-system \
  -f custom-gateway-values.yaml \
  --wait
```

## Troubleshooting

### Certificate Issues

```bash
# Check certificate events
kubectl describe certificate demo-app-tls -n istio-system

# Check cert-manager logs
kubectl logs -n cert-manager -l app.kubernetes.io/name=cert-manager --tail=50
```

### Gateway Issues

```bash
# Check gateway configuration
istioctl analyze -n istio-system

# Check ingress gateway logs
kubectl logs -n istio-system -l app=istio-ingressgateway --tail=50
```

### mTLS Issues

```bash
# Check PeerAuthentication policy
kubectl describe peerauthentication -n my-demo

# Check if sidecars are properly injected
kubectl get pods -n my-demo -o wide

# Check service mesh connectivity
istioctl proxy-status
```

### Service Connectivity Issues

```bash
# Check service endpoints
kubectl get endpoints -n my-demo

# Check service discovery
istioctl proxy-config endpoints -n my-demo <pod-name>

# Test internal service communication
kubectl exec -n my-demo <frontend-pod> -c frontend-app -- curl backend-app:8080/health
```

## Security Features Enabled

✅ **TLS Termination**: HTTPS traffic terminated at Istio Gateway
✅ **Certificate Management**: Automatic certificate renewal via cert-manager  
✅ **HTTP Redirect**: All HTTP traffic redirected to HTTPS
✅ **Strict mTLS**: Encrypted communication between all services
✅ **Service-to-Service Auth**: Istio handles authentication between services

## Next Steps

1. **Monitor certificate renewal** - Check cert-manager logs periodically
2. **Set up observability** - Configure Istio metrics and tracing
3. **Add authorization policies** - Define fine-grained access controls
4. **Production hardening** - Review security settings for production use

Your E2E encryption setup is now complete! 🎉

## Helm Chart Structure

```
helm-charts/istio-encryption-config/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Simple enable/disable toggles
└── templates/
    ├── _helpers.tpl              # Template helpers
    ├── NOTES.txt                 # Post-install instructions
    ├── certificate.yaml          # TLS certificate for gateway
    ├── gateway.yaml              # Istio Gateway resource
    ├── virtual-service.yaml      # Traffic routing rules
    ├── destination-rule.yaml     # Service policies (mTLS)
    └── peer-authentication.yaml  # Strict mTLS enforcement
```