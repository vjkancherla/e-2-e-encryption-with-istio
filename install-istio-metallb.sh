#!/bin/bash

# Function to print section headers
print_section() {
  echo -e "\n\033[1;34m==> $1\033[0m"
}

# Function to print status messages
print_status() {
  echo -e "\033[1;32m[+] $1\033[0m"
}

# Function to print informational messages
print_info() {
  echo -e "\033[1;36m[i] $1\033[0m"
}

# Function to print warning messages
print_warning() {
  echo -e "\033[1;33m[!] $1\033[0m"
}

# Function to print error messages and exit
print_error() {
  echo -e "\033[1;31m[x] $1\033[0m"
  exit 1
}

# Function to wait for pods to be ready
wait_for_pods() {
  local namespace=$1
  local selector=$2
  local count=$3
  local timeout=300
  local start_time=$(date +%s)

  print_info "Waiting for $count pods with selector '$selector' in namespace '$namespace' to be ready..."
  
  while true; do
    local ready=$(kubectl get pods -n "$namespace" --selector="$selector" \
      --field-selector=status.phase=Running -o jsonpath='{.items[*].status.containerStatuses[?(@.ready)].name}' | wc -w)
    
    if [ "$ready" -ge "$count" ]; then
      print_status "All $count pods are ready!"
      return 0
    fi

    local current_time=$(date +%s)
    local elapsed=$((current_time - start_time))
    
    if [ "$elapsed" -gt "$timeout" ]; then
      print_warning "Timeout reached while waiting for pods to be ready"
      return 1
    fi
    
    sleep 5
  done
}

# Main execution
print_section "Starting MetalLB an Istio Installation"
print_info "This script will install all required components for Istio"

print_section "Installing MetalLB (Load Balancer)"
print_status "Adding MetalLB Helm repository..."
helm repo add metallb https://metallb.github.io/metallb || print_error "Failed to add MetalLB Helm repo"
helm repo update || print_error "Failed to update Helm repos"

print_status "Installing MetalLB..."
helm upgrade --install my-metallb metallb/metallb \
  --version 0.15.2 \
  --namespace metallb-system \
  --create-namespace || print_error "Failed to install MetalLB"
print_status "MetalLB installed"

print_status "Waiting for MetalLB pods to be ready..."
if wait_for_pods "metallb-system" "app.kubernetes.io/instance=my-metallb" 3; then
  print_status "Applying MetalLB IP pool configuration..."
  cat <<EOF | kubectl apply -f - || print_error "Failed to apply MetalLB IP pool"
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 172.19.255.200-172.19.255.250
EOF

  cat <<EOF | kubectl apply -f - || print_error "Failed to apply MetalLB L2 advertisement"
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default-advertise
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
EOF
  print_status "MetalLB configuration applied successfully"
else
  print_error "MetalLB pods did not become ready within the timeout period"
fi

print_section "Installing Istio Components"
print_status "Adding Istio Helm repository..."
helm repo add istio https://istio-release.storage.googleapis.com/charts || print_error "Failed to add Istio Helm repo"
helm repo update || print_error "Failed to update Helm repos"

print_status "Installing Istio base components..."
helm upgrade --install istio-base istio/base \
  --version 1.26.2 \
  -n istio-system \
  --create-namespace \
  --wait || print_error "Failed to install Istio base"
print_status "Istio base installed"

print_status "Waiting for Istio base to stabilize..."
sleep 30

print_status "Installing Istio control plane (istiod)..."
helm upgrade --install istiod istio/istiod \
  --version 1.26.2 \
  --namespace istio-system \
  --wait || print_error "Failed to install Istio control plane"
print_status "Istio control plane installed"

print_status "Installing Istio ingress gateway..."
helm upgrade --install istio-ingressgateway \
  istio/gateway \
  --version 1.26.2 \
  --namespace istio-ingress \
  --create-namespace \
  --wait || print_error "Failed to install Istio ingress gateway"
print_status "Istio ingress gateway installed"


print_section "Verification"
print_status "Checking installed components..."
echo -e "\n\033[1;33mCluster nodes:\033[0m"
kubectl get nodes

echo -e "\n\033[1;33mIstio components:\033[0m"
kubectl get pods -n istio-system
kubectl get pods -n istio-ingress

echo -e "\n\033[1;33mMetalLB:\033[0m"
kubectl get pods -n metallb-system

print_section "Installation Complete"
print_info "All prerequisites have been installed successfully!"