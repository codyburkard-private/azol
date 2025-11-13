---
layout: default
title: Azol Documentation
---

# Azol - Azure Offensive Library

Azol is a Python-based pentesting library for Azure and Entra ID. It provides a comprehensive set of tools for interacting with Azure services, managing authentication, and performing security assessments.

## Overview

Azol simplifies Azure security testing by providing:

- **Multiple Authentication Methods**: Support for user credentials, service principals, access tokens, and more
- **Comprehensive API Clients**: Pre-built clients for ARM, Graph API, Key Vault, Azure DevOps, and more
- **Token Management**: Automatic token caching and refresh handling
- **Easy Auth Utilities**: Tools for working with Azure App Service Easy Auth
- **Certificate Management**: X.509 certificate creation and management

## Key Features

- 🔐 **Flexible Authentication**: Multiple credential types and OAuth flows
- 🚀 **Easy to Use**: Simple, intuitive API design
- 🔄 **Token Caching**: Automatic token management with persistent caching
- 🛠️ **Comprehensive Coverage**: Support for major Azure services
- 📦 **Well Documented**: Extensive documentation and examples

## Quick Example

```python
from azol.credentials import User
from azol.clients import ArmClient

# Authenticate as a user
cred = User(username="user@domain.com")
arm_client = ArmClient(tenant="tenant.com", cred=cred)

# Get all subscriptions
subscriptions = arm_client.get_subscriptions()

for sub_id in subscriptions:
    print(sub_id)
```

## Getting Started

1. [Install Azol](/installation)
2. [Read the Quick Start Guide](/quick-start)
3. [Explore the API Documentation](/clients)

## Documentation Sections

- **[Installation](/installation)**: How to install Azol
- **[Quick Start](/quick-start)**: Basic usage examples
- **[Clients](/clients)**: API client documentation
- **[Credentials](/credentials)**: Authentication and credential management
- **[Utilities](/utilities)**: Helper functions and utilities
- **[Providers](/providers)**: Secret providers
- **[Caches](/caches)**: Token caching mechanisms
- **[Models](/models)**: Data models and classes

## License

See the [LICENSE](https://github.com/cdburkard/azol/blob/main/LICENSE) file for details.

## Contributing

Contributions are welcome! Please see the [GitHub repository](https://github.com/cdburkard/azol) for more information.

