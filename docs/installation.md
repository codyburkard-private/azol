---
title: Installation
nav_order: 0
---

# Installation

## Requirements

- Python 3.6 or higher
- pip (Python package installer)

## Install from PyPI

The easiest way to install Azol is using pip:

```bash
pip install azol
```

## Install from Source

If you want to install from the source code:

```bash
git clone https://github.com/cdburkard/azol.git
cd azol
pip install .
```

## Dependencies

Azol has the following dependencies (installed automatically):

- `requests==2.31.0` - HTTP library for API requests
- `dataclasses==0.6` - Data class support
- `cryptography` - Cryptographic operations

## Verify Installation

To verify that Azol is installed correctly:

```python
import azol
print(azol.__version__)  # If version is available
```

Or try importing a client:

```python
from azol.clients import ArmClient
from azol.credentials import User

print("Azol installed successfully!")
```

## Next Steps

After installation, check out the [Quick Start Guide](/quick-start) to begin using Azol.

