---
title: Clients
nav_order: 1
---

## Available Clients

- [OAuthHTTPClient](oauthhttpclient) - Base class for all OAuth HTTP clients
- [ArmClient](armclient) - Azure Resource Manager API client
- [GraphClient](graphclient) - Microsoft Graph API client
- [KeyVaultClient](keyvaultclient) - Azure Key Vault client
- [AzureDevOpsClient](azuredevopsclient) - Azure DevOps API client
- [DataFactoryClient](datafactoryclient) - Azure Data Factory API client
- [KuduClient](kuduclient) - Kudu/SCM API client
- [AzureDevOpsAgentClient](azuredevopsagentclient) - Azure DevOps Agent client

# Azol Clients

Azol clients are the primary interface for interacting with the various services and apis that are supported by the library. For example, the GraphClient is an interface towards the Graph API, and the ArmClient is an interface towards the ARM API.

## Credentials 

A client requires a "cred" parameter on initialization, where the credential parameter defines a credential type which the client may use to authenticate to the backend API. Often, an API supports authentication via several different credential types. The azol client usage should not differ based on which credential is used. For example:

```
Case 1: Authenticate with User credential

from azol import *
credential = User("myuser@mydomain.com")
client = GraphClient(cred=user, use_token_broker=True)
client.get_all_users()

Case 2: Authenticate with Service Principal credential

from azol import *
credential = ServicePrincipal(client_id="11111111-2222-3333-4444-555555555555", client_secret="SPSecret123")
client = GraphClient(cred=user, use_token_broker=True)
client.get_all_users()

```

Assuming that both the user and the service principal have access to read the users from the Graph API, both of these scripts will return the same contents.

## OAuthHTTPClient and Entra ID credentials

The OAuthHTTPClient is the base class of many of the clients within Azol. It provides the piping for interacting with the Microsoft Identity Platform via OAuth. Underneath the hood, it initializes a "TokenService" which handles all of the Authentication headers, token management, token caching, and OAuth requests for requesting and renewing Access and Refresh tokens. For the most part, it should be invisible to the user, but it also provides internal access to OAuth access and refresh tokens that are not available within the Microsoft libraries due to security reasons.

For example, the OAuthHTTPClient supports the following capabilities that are useful for abuse scenarios, that wont be found in a normal "production" library:

- Direct access to the currently used refresh token
- Ability to switch tenants using the currently cached refresh token
- Ability to switch *OAuth Clients* via the currently cached refresh token
- Ability to switch *OAuth Resources* via the currently cached refresh token

All clients that inherit from the OAuthHTTPClient base class support the following credential types, along with any custom types that are specific to the backend API:

- User
- ServicePrincipal
- Application

## OAuth semantics and azol client objects

Terminology can become a bit confusing when combining the idea of an azol client and an OAuth client. This section will briefly explain how to think about these concepts within azol.

In azol, a client object represents an *HTTP Client* for some specific backend API or service. In OAuth semantics, you also have the idea of a client, which is an *OAuth Client* that represents some application.

In an azol OAuthHTTPClient, both of these concepts are represented - the azol OAuthHTTPClient is an HTTP client toward some backend API, but it accepts a credential parameter that may specify an OAuth Client. In practice this is initialized as follows:

```
from azol import *

# Here, client_id is the OAuth client
user=User(username="user@domain.com", client_id="00000000-1111-2222-3333-444444444444") 

# Here, the GraphClient is the azol HTTP Client, which inherits from OAuthHTTPClient.
client=GraphClient(cred=user)

# Here, the azol client will execute an OAuth flow to get a new access token for the OAuth client_id in *user*
# against the Microsft Graph OAuth Resource (https://graph.microsoft.com). 
client.fetch_token()

# Note that the request will fail unless the client_id exists in the tenant and has
# been consented to Microsoft Graph. By default, azol uses a first-party Azure Powershell 
# client_id for users, which causes the library to spoof logins and session for the 
# Azure Powershell CLI.

```

#### *Why is client_id in the User object?*

In reality, this makes little sense within OAuth semantics. The client_id should represent an OAuth client, which should be its own app such as Azure CLI, Azure Portal, etc.

However, azol is a security testing library, not a library that is supposed to follow OAuth semantics and best practices. By including client_id in the credential object, we can completely decouple the credential from the client. This is useful when managing different stolen sessions during an engagement, and makes the azol client usage consistent across different credential types. For example, consider the following two azol credentials:

- ServicePrincipal(client_id=etc, client_secret=etc)
- User(username=etc, client_id=etc)

From a security testing angle, it makes sense to combine a client_id and client_secret into a single credential object for tracking and management. If we were to specify the client_id for the user within the client object instead of a credential object, this complicates the API and would create inconsistencies within client usage across different credentials, which we want to avoid.

### OAuth Flows

The OAuthHTTPClient supports the following login flows:

- **Client Credential Grant** (Default for service principals and Application Objects) - The OAuth client credential grant
- **Device Code** (default for User objects where no Refresh Token is provided) - the OAuth device code flow
- **Refresh Token** - (default for User objects where a Refresh Token is provided) The OAuth refresh token flow. Can be used if the credential is a User and a refresh token is already known
- **Raw Token** - Used if the initial credential is a raw access token, where no OAuth flow is required for use.
- **Authorization Code** - The OAuth authorization code flow. 

## Client Method Response Contents

Generally, azol clients provide a very low-level interface to backend APIs. Azol does not maintain response models for most methods, and simply deserializes the JSON responses that are returned by the backend API, and returns those responses to the user.

This means that for some methods, there is some inherent instability in the library. If Microsoft quietly changes and API, it could cause the response contents from an azol method to return a new value. This shouldnt be a problem for clients liek GraphClient and ArmClient, which are versioned, but may be problematic in undocumented APIs that azol supports, such as the AzureDevopsAgentClient.

## Handling API errors in azol clients

If an HTTP error is returned to the client from the backend API, this is often due to issues such as a missing permission. Azol does its best to catch these errors and throw an exception towards the user, which includes the raw response collected from the backend API. Wrap client calls in try: ... catch: ... blocks when writing scripts in order to catch these errors. 


