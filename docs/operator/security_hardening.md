# Security Hardening Guide

This document outlines best practices for securing Null-Lang deployments, including threat modeling, configuration, and supply chain security.

## Threat Model

Operators should consider the following threats:

1.  **Code Injection**: Malicious Null-Lang code executed via dynamic evaluation (avoid `eval()` on untrusted input).
2.  **Dependency Vulnerabilities**: Vulnerabilities in third-party libraries or the Null-Lang runtime itself.
3.  **Privilege Escalation**: Running the VM with excessive permissions (e.g., `root`).
4.  **Data Leakage**: Sensitive data exposed in logs or error messages.

## Security Configuration

### Runtime Configuration
- **Run as Non-Root**: Always run the VM container as a non-root user.
- **Read-Only Filesystem**: Mount the application code as read-only.
- **Resource Limits**: Set CPU and Memory limits to prevent DoS (see Deployment Guide).

### Encryption
- **Data in Transit**: Use TLS for all network communications. Terminate TLS at the load balancer or ingress.
- **Data at Rest**: Encrypt sensitive data in databases and configuration stores.

## Supply Chain Security

### SBOM (Software Bill of Materials)
Generate an SBOM for your application to track dependencies.

```bash
# Example using Syft
syft packages dir:. -o spdx-json > sbom.json
```

### Dependency Scanning
Regularly scan your container images and dependencies for known vulnerabilities.

**Trivy Example**:
```bash
trivy image my-null-app:latest
```

**CI/CD Integration**:
Fail the build if critical vulnerabilities are found.

```yaml
- name: Scan Image
  run: trivy image --exit-code 1 --severity CRITICAL my-null-app:latest
```

## Audit Guidance

Enable audit logging to track critical actions.

- **Access Logs**: Record all incoming HTTP requests.
- **System Logs**: Monitor VM startup/shutdown and error events.
- **Change Management**: Audit all changes to production configuration and code.

## Secret Management

NEVER store secrets in source code or docker images.
- Use **Environment Variables** (injected securely) or **Files mounted via Secrets**.
- Access secrets at runtime using `std::env::var("SECRET_NAME")`.
