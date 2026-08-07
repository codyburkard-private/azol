from setuptools import setup, find_packages
import os


readmeText=""
with open("README.md", "r") as f:
    readmeText+=f.read()

setup(
    name='azol',
    version=version,
    packages=find_packages(),
    url='https://github.com/cdburkard/azol',
    author='Cody Burkard',
    description='A python-based pentesting library for Azure and Entra ID',
    long_description=readmeText,
    long_description_content_type="text/markdown",
    install_requires=[
        "requests==2.31.0",
        "cryptography==50.0.0",
        "pymsalruntime==0.2.0.6; platform_system == 'Windows'",
        "dataclasses==0.6",
    ],
    extras_require={
        "docs": [
            "mkdocs-material>=9.0",
            "mkdocstrings[python]>=0.24",
        ],
    },
)