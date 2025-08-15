# Cert-Manager Installation Guide

This guide will help you install and configure cert-manager for your Istio E2E encryption PoC using Helm charts.

## Prerequisites

- K3D cluster running
- kubectl configured to access your cluster
- Helm 3 installed

## Step 1: Install cert-manager

```bash
# Add the Jetstack Helm repository
helm repo add jetstack https://charts.jetstack.io

# Update your local Helm chart repository cache
helm repo update

# Install cert-manager with CRDs
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.13.3 \
  --set installCRDs=true \
  --set global.leaderElection.namespace=cert-manager
```

## Step 2: Verify Installation

```bash
# Check if cert-manager pods are running
kubectl get pods --namespace cert-manager

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s

# Verify cert-manager is working
kubectl get crd | grep cert-manager
```

Expected output should show cert-manager CRDs:
```
certificaterequests.cert-manager.io
certificates.cert-manager.io
challenges.acme.cert-manager.io
clusterissuers.cert-manager.io
issuers.cert-manager.io
orders.acme.cert-manager.io
```

## Step 3: Deploy cert-manager Configuration Helm Chart

Now deploy the cert-manager configuration using your custom Helm chart:

```bash
# Create the my-demo namespace if it doesn't exist
kubectl create namespace my-demo --dry-run=client -o yaml | kubectl apply -f -

# Install the cert-manager configuration chart
helm install cert-manager-config ./helm-charts/cert-manager-config \
  --namespace cert-manager \
  --wait

# Run the test to verify everything is working
kubectl get certificate -n cert-manager

# View detailed status
kubectl describe certificate test-cert -n cert-manager

# Check certificate secret
kubectl get secret test-cert-secret -n cert-manager
```

### Alternative: Deploy with custom values

If you want to customize the configuration, create a custom values file:

```bash
# Create custom values (optional)
cat > custom-cert-values.yaml << EOF
caCertificate:
  commonName: "My Custom Root CA"
  organization: "Your Company"

testCertificate:
  enabled: true
  commonName: demo-app.127.0.0.1.nip.io
  dnsNames:
    - demo-app.127.0.0.1.nip.io
    - test.127.0.0.1.nip.io
EOF

# Install with custom values
helm install cert-manager-config ./helm-charts/cert-manager-config \
  --namespace cert-manager \
  -f custom-cert-values.yaml \
  --wait
```

## Step 4: Verify cert-manager Setup

```bash
# Check if cert-manager pods are running
kubectl get pods --namespace cert-manager

# Check certificates status
kubectl get certificate -n cert-manager

# Check ClusterIssuers
kubectl get clusterissuer

# View detailed certificate information
kubectl describe certificate ca-certificate -n cert-manager
kubectl describe certificate test-cert -n cert-manager

# Verify certificate secrets were created
kubectl get secret ca-key-pair -n cert-manager
kubectl get secret test-cert-secret -n cert-manager

# Test certificate content (optional)
kubectl get secret test-cert-secret -n cert-manager -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -text | head -20
```

Expected output should show both certificates with `Ready=True` status.

## Step 5: Manual Testing (If Needed)

The Helm chart includes automatic testing, but you can also test manually:

```bash
# Create a manual test certificate
kubectl apply -f - << EOF
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: manual-test-cert
  namespace: my-demo
spec:
  secretName: manual-test-cert-secret
  commonName: manual-test.127.0.0.1.nip.io
  dnsNames:
  - manual-test.127.0.0.1.nip.io
  issuerRef:
    name: ca-issuer
    kind: ClusterIssuer
    group: cert-manager.io
EOF

# Check if certificate was issued
kubectl get certificate manual-test-cert -n my-demo
kubectl describe certificate manual-test-cert -n my-demo

# Clean up manual test certificate
kubectl delete certificate manual-test-cert -n my-demo
```

## Troubleshooting

### Common Issues

1. **Pods not starting**: Check if you have sufficient resources in your K3D cluster
2. **CRDs not found**: Ensure CRDs were installed properly with cert-manager
3. **Webhook issues**: Wait a few minutes for webhooks to become available
4. **Test failures**: Check if the my-demo namespace exists and cert-manager is fully ready
5. **Chart installation fails**: Ensure cert-manager is installed first

### Useful Commands

```bash
# Check cert-manager logs
kubectl logs -n cert-manager -l app.kubernetes.io/name=cert-manager

# Check webhook logs
kubectl logs -n cert-manager -l app.kubernetes.io/name=webhook

# Check CA injector logs
kubectl logs -n cert-manager -l app.kubernetes.io/name=cainjector

# Describe a certificate for debugging
kubectl describe certificate <certificate-name> -n <namespace>

# Check certificate events
kubectl get events -n <namespace> --field-selector involvedObject.kind=Certificate

# Debug Helm test
kubectl logs -n my-demo -l job=cert-test

# Check Helm test status
kubectl get jobs -n my-demo -l job=cert-test
```

## Helm Chart Structure

The cert-manager configuration is now managed by a Helm chart located at:
```
helm-charts/cert-manager-config/
├── Chart.yaml                           # Chart metadata
├── values.yaml                          # Default configuration values
└── templates/
    ├── _helpers.tpl                     # Template helpers
    ├── NOTES.txt                        # Installation notes with verification steps
    ├── cluster-issuer.yaml              # ClusterIssuer resources
    ├── ca-certificate.yaml              # CA Certificate resource
    ├── test-certificate.yaml            # Test certificate (validates setup)
    └── test-namespace.yaml              # Test namespace (if needed)
```

## Next Steps

After cert-manager is installed and working:

1. Configure Istio Gateway with TLS
2. Create certificates for your domain (`demo-app.127.0.0.1.nip.io`)
3. Set up VirtualService and DestinationRule
4. Enable mTLS with PeerAuthentication

Your cert-manager installation is now complete and ready for the next phase of your Istio E2E encryption setup!d DestinationRule
4. Enable mTLS with PeerAuthentication

Your cert-manager installation is now complete and ready for the next phase of your Istio E2E encryption setup!

## Files Created

Make sure to save these files in your project:
- `cluster-issuer.yaml` - Self-signed and CA cluster issuers
- `ca-certificate.yaml` - Root CA certificate
- `test-certificate.yaml` - Optional test certificate

You can organize these in a `cert-manager/` directory in your repository.