---
title: Caches
nav_order: 6
---

# Token Caching

Azol provides token caching mechanisms for any class that inherits from OAuthHTTPClient to avoid unnecessary authentication requests. 

There are two levels of caching:

1) In-memory caching: The azol client object caches the most recent access token, and uses that access token until it expires. 

2) Persistent, on-disk caching: The azol library has a default on-disk cache where tokens are stored. This cache is used for persistent session management across azol runs.

## Persistent Cache

The peristent token cache is stored in the *~/.azol/token_cache/default* file.

This file contains all oauth refresh and access tokens that have been used by azol. It can be used by sending the *use_persistent_cache=True* parameter to an OAuthHTTPClient, and is enabled by default.

If this cache is not disabled, the client will search the cache for any relevant token prior to sending a new authorization request. It matches on client_id, resource, scope, and user. If a cache entry is found and the token is not expired, the client will try to use that token or refresh token.

## Cache Management

### Clearing Cache

To clear the local cache, just delete the cache file 

### Dont want to use the cache?

Just set *use_persistent_cache=False* in the client constructor
