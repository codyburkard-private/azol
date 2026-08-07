"""A module containing an azol key vault http client"""
from typing import Any
from azol.clients.oauth_http_client import OAuthHTTPClient
from azol.constants import KEYVAULTAPIVERSION, OAuthResourceIDs
from azol.http import HttpCall


class KeyVaultClient( OAuthHTTPClient ):
    """
        An HTTP client for interacting with Azure key vaults.
        Works with all credential objects
    """

    def __init__( self, key_vault_name: str, *args, **kwargs ):
        key_vault_resource_id=OAuthResourceIDs.KeyVault
        kv_base_url=f"https://{key_vault_name}.vault.azure.net"
        super().__init__( oauth_resource=key_vault_resource_id,
                          base_url=kv_base_url, *args, **kwargs)
        self.kv_name = key_vault_name

    def call(self, path: str) -> HttpCall:
        """Return a fluent Key Vault call bound to this client.

        Failures raise ``AzolHTTPError`` (or a status-specific subclass).
        """
        return HttpCall(self, path, next_link_key="nextLink")

    def get_keys( self ) -> list[Any]:
        """Get all keys in the key vault.

        Get all keys from the key vault connected to this client,
        which the credential object can access.

        Returns:
           List of key objects from the key vault

        Raises:
            AzolHTTPError: An error occurred accessing the Key Vault API
        """
        return (
            self.call("/keys")
            .api_version(KEYVAULTAPIVERSION)
            .get()
            .values()
        )

    def get_secret( self, secret_name: str, secret_version: str | None=None ) -> list[Any]:
        """Get a secret from the key vault.

        Args:
            - secret_name - (string) The name of the secret
            - secret_version - (string) defaults to None. the version of the secret, or 
                               None if requesting the most recent
        
        Returns:
           Secret value string from the key vault

        Raises:
            AzolHTTPError: An error occurred accessing the Key Vault API
        """
        if secret_version is None:
            path = f"/secrets/{secret_name}"
        else:
            path = f"/secrets/{secret_name}/{secret_version}"
        return (
            self.call(path)
            .api_version(KEYVAULTAPIVERSION)
            .get()
            .json()["value"]
        )

    def get_secrets( self ) -> list[Any]:
        """Get all secrets in the key vault.

        Get all secrets from the key vault connected to this client,
        which the credential object can access.

        Returns:
           List of secret objects from the key vault

        Raises:
            AzolHTTPError: An error occurred accessing the Key Vault API
        """
        return (
            self.call("/secrets")
            .api_version(KEYVAULTAPIVERSION)
            .get()
            .values()
        )

    def get_certificates( self ) -> list[Any]:
        """Get all certificates in the key vault.

        Get all certificates from the key vault connected to this client,
        which the credential object can access.

        Returns:
           List of certificate objects from the key vault

        Raises:
            AzolHTTPError: An error occurred accessing the Key Vault API
        """
        return (
            self.call("/certificates")
            .api_version(KEYVAULTAPIVERSION)
            .get()
            .values()
        )
