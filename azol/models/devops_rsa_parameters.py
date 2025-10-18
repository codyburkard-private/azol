"""A module containing RSA parameters for Azure DevOps agents"""
from dataclasses import dataclass

@dataclass
class DevOpsRSAParameters:
    """
        A dataclass containing RSA key parameters for Azure DevOps agent authentication
    """
    p: bytes
    q: bytes
    d: bytes
    modulus: bytes
    dp: bytes
    dq: bytes
    exponent: bytes
    inverseq: bytes
