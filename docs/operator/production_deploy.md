# Production Deployment Guide for Null-Lang

This guide provides authoritative documentation for deploying Null-Lang applications in production environments, covering Docker, Kubernetes, and Cloud providers.

## Docker Images

Null-Lang provides official Docker images for running the VM and compiler.

### Base Images

- `null-lang/runtime:latest` - Minimized runtime environment (VM + SuperBit loader)
- `null-lang/sdk:latest` - Full development kit (Compiler, VM, Tools)
- `null-lang/ml:latest` - Runtime with pre-installed ML dependencies (PyTorch, TorchVision)

### Building Your Application Image

Create a `Dockerfile` for your Null-Lang application:

```dockerfile
FROM null-lang/runtime:latest

WORKDIR /app
COPY . .

# Install dependencies
RUN null-pkg install

# Entrypoint
CMD ["null-vm", "run", "main.null"]
```

## Kubernetes Manifests

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: null-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: null-app
  template:
    metadata:
      labels:
        app: null-app
    spec:
      containers:
      - name: null-app
        image: my-registry/my-null-app:v1
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        env:
        - name: NULL_ENV
          value: "production"
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: null-app-svc
spec:
  selector:
    app: null-app
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

## Cloud Checklist

When deploying to cloud providers (AWS, GCP, Azure), ensure the following:

1.  **IAM Roles**: Grant least-privilege access to resources (S3 buckets, DynamoDB, etc.).
2.  **Networking**: Run VM instances in private subnets behind a Load Balancer / Ingress.
3.  **Secrets Management**: Use Secrets Manager (AWS), Secret Manager (GCP), or Key Vault (Azure) instead of environment variables for sensitive data.
4.  **Logging**: Configure log drivers to ship stdout/stderr to CloudWatch/Stackdriver.

## Scaling Tips

### Horizontal Scaling
Null-Lang VMs are stateless by default. Scale out by increasing replica count based on CPU utilization or request latency.

### Vertical Scaling
For ML workloads using the `null-lang/ml` image, ensure sufficient memory and consider GPU-enabled instances.

### Optimization
- Enable SuperBit JIT for long-running processes.
- Use the `docs/operator/api_reference.md` to identify heavy modules that can be optimized or offloaded.
