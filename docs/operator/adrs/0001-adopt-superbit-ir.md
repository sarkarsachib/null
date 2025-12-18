# Adopting SuperBit IR for Production Workloads

*   **Status**: Accepted
*   **Date**: 2023-10-27
*   **Authors**: Architecture Team

## Context

The Null-Lang platform supports both interpreted execution (AST-walking) and JIT-compiled execution via SuperBit IR. While AST interpretation is simpler and faster for development iteration, it lacks the performance and optimization capabilities required for high-throughput production workloads, particularly those involving ML and numerical computing.

## Decision

We will adopt SuperBit IR as the standard execution format for all production deployments of Null-Lang applications.

1.  All production artifacts must be compiled to SuperBit bytecode (`.sbit`) before deployment.
2.  The production runtime (`null-vm`) will default to JIT-compiling SuperBit IR.
3.  The CI/CD pipeline will include a compilation step that fails if SuperBit generation fails.

## Consequences

### Positive
*   **Performance**: Significant performance improvements for compute-intensive tasks due to JIT optimizations.
*   **Security**: Bytecode verification layer adds a security check before execution.
*   **Portability**: SuperBit IR is platform-independent, simplifying cross-platform deployments.

### Negative
*   **Build Time**: Adds a compilation step to the deployment pipeline, slightly increasing build times.
*   **Complexity**: Debugging compiled bytecode can be more difficult than debugging source code directly (though source maps mitigate this).

### Risks
*   **Compatibility**: Some dynamic features of the language may behave differently or require specific annotations to work correctly in compiled mode.
