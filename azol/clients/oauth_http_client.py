"""Module containing a parent class for an azol http client"""
import uuid
import logging
from azol.utils import is_token_expired, get_tenant_id, parse_jwt
from azol.services.token_service import TokenService as tService
from azol.credentials import User
from azol.constants import UserAgents, OAUTHFLOWS, known_client_redirect_uris
from azol.http import OAuthRequestBuilder, create_session
from azol.http.session import DEFAULT_TIMEOUT

class OAuthHTTPClient:
    """
        Base class for OAuth HTTP client objects.
    """

    def __init__( self, cred, oauth_resource, base_url=None, redirect_uri=None,
                  tenant=None, azol_id=None, oauth_flow=None, secrets_provider=None,
                  use_persistent_cache=True, auto_refresh=True, scopes=[], use_token_broker=False,
                  useragent=UserAgents.Windows_Edge, session=None, request_timeout=DEFAULT_TIMEOUT):
        if tenant is None:
            if cred.credentialType != "user":
                raise Exception("tenant must be specified if credential is not of type 'user'")
            if not cred.default_oauth_flow=="refresh_token":
                username=cred.get_username()
                tenant=username.split("@")[1]
            else:
                if cred.username_is_known():
                    username=cred.get_username()
                    tenant=username.split("@")[1]
        self.use_token_broker=use_token_broker
        self.scopes=scopes
        self._useragent=useragent
        self.default_scope=True
        self.profile_scope=True
        self.openid_scope=True
        self.offline_access_scope=True
        self._baseurl = base_url
        self._request_timeout = request_timeout
        self._owns_session = session is None
        self._session = session if session is not None else create_session(
            user_agent=useragent
        )

        self._tenant = tenant
        self._resource = oauth_resource
        self._current_token = None

        # if no specific oauth flow is provided, get the default from the credential
        if oauth_flow is None:
            oauth_flow=cred.get_default_oauth_flow()
        if oauth_flow == OAUTHFLOWS.AUTHORIZATION_CODE or use_token_broker:
            if redirect_uri == None:
                client_id = cred.get_client_id()
                logging.info(f"No redirect URI supplied. Checking for known"
                              " redirect URIs for client id {client_id}...")
                if client_id not in known_client_redirect_uris.keys():
                    logging.error(f"No redirect URI found for client id {client_id}")
                    raise Exception("A redirect URI must be supplied")
                else:
                    redirect_uri=known_client_redirect_uris[client_id][0]
                    logging.info(f"Redirect URI found. Using first redirect in list:"
                                 f"{redirect_uri}")

        self.token_service = tService( cred, tenant_id=tenant, oauth_flow=oauth_flow,
                                    use_token_broker=use_token_broker,
                                    secrets_provider=secrets_provider,
                                    use_persistent_cache=use_persistent_cache,
                                    oauth_resource=oauth_resource, scopes=self.scopes,
                                    default_scope=self.default_scope,
                                    profile_scope=self.profile_scope,
                                    openid_scope=self.openid_scope,
                                    offline_access_scope=self.offline_access_scope,
                                    redirect_uri=redirect_uri,
                                    useragent=useragent )

        self._current_token = self.token_service.get_cached_token_if_not_expired()

        self._auto_refresh=auto_refresh
        if azol_id is None:
            azol_id = str(uuid.uuid4())
        self._id=azol_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        """Close the underlying ``requests.Session`` if this client owns it."""
        if getattr(self, "_owns_session", False) and getattr(self, "_session", None) is not None:
            self._session.close()
            self._session = None

    def get_token_claims( self ):
        """Get claims in the current token

        parses the cached token and returns the body

        Returns:
           A dictionary containing the unencoded token body, or None if no token

        """
        token = self.get_current_token()

        if token is None:
            return None
        
        header, body, signature = parse_jwt(token)

        return body

    def switch_tenant(self, tenant):
        """
            Switch the tenant of the client.
            This nullifies the current token of the client, and subsequent requests
            will be made to the new tenant

            Args:
                - tenant - (string)  a tenant id or domain name for a tenant
            Returns:
                None
        """
        # get the tenant Id if its a domain name. If it cant be parsed as a guid, its a domain name.
        try:
            uuid.UUID(tenant, version=4)
        except ValueError:
            tenant=get_tenant_id(tenant)

        self._current_token=None
        self.token_service.set_tenant(tenant)
        self._tenant=tenant

    def switch_scope(self, scopes, default, profile, offline_access, openid):
        """
            Change the scope of the OAuth client. This will cause a new scope to be requested
            on subsequent tokens, and will nullify the current token.

            Args:
                - scopes - a list containing a list of oauth scopes to request
                - default - bool, if the default scope should be requested. 
                              this overrides any other scope set
                - profile - bool, if the profile scope should be requested
                - offline_access - bool, if the offline_access scope should be requested
                - openid - bool, if the openid scope should be requested

            Returns:
                None
        """
        self._current_token=None
        self.token_service.set_scope(scopes, default, profile, offline_access, openid)
        self.scopes=scopes
        self.default_scope=default
        self.profile_scope=profile
        self.offline_access_scope=offline_access
        self.openid_scope=openid

    def get_id(self):
        """
            Get the azol ID of the client

            Returns:
                 string
        """
        return self._id

    def refresh_token( self ):
        """
            force the token cache to use the refresh token in the current credential to
            generate a new access token

            Returns:
                None
        """
        self._current_token = self.token_service.refresh_token()

    def get_current_refresh_token( self ):
        """
            Get the current refresh token in use by the client

            Returns:
                string - ascii representation of refresh token
        """
        token=self.token_service.get_refresh_token_if_exists()
        return token

    def fetch_token(self):
        """
            Fetch a new token. Save the token as the current token to be used by the client

            Args:
                - scope - (string) a space-separated list of scopes to request for the new token

            Returns:
                None
        
        """
        # token service needs to "log in" and cache the token.
        # if the credential is a user credential, also possible cache the refresh token
        access_token=self.token_service.fetch_token()
        self._current_token = access_token
        return None

    def get_current_token(self):
        """
            Get the current token being used by the client

            Returns:
                raw ascii representation of the current token or None if no token is saved
        """
        if self._current_token is None:
            return None

        return self._current_token

    def get_client_id( self ):
        return self.token_service.get_client_id()

    def switch_client(self, client_id):
        """
            Switch the oauth client used by the HTTP Client. Used to abuse FOCI functionality.

            nullifies current cached access token, but leaves refresh token in client.

            Vars:
                - client_id - the client id of the client that we will switch to.

            Returns:
                OAuthHTTPClient subclass
        """
        self._current_token = None
        self.token_service.switch_client(client_id)

    @classmethod
    def from_client(cls, client, *args, **kwargs):
        """
            Generate a new HTTP Client with a different OAuth Resource, using the current client class.

            Use this class to switch from, for example, a GraphClient to an ArmClient.
            Nullifies current cached access token, but leaves refresh token in client.

            Note: alternative to "refresh_to_new_resource" of an active client, but results in the same.

            Vars:
                - client - OAuthHTTP child class that will be used to instantiate the 
                              new class. Note that this must be a valid
                              OAuth HTTP child class. For example, ArmClient, GraphClient,
                              or KeyVaultClient

            Returns:
                OAuthHTTPClient subclass instance
        """
        rt = client.get_current_refresh_token()
        user = User(refresh_token=rt, client_id=client.get_client_id())
        newClass = cls(*args, tenant=client._tenant, cred=user, **kwargs)
        return newClass

    def refresh_to_new_resource(self, oauth_http_client_class):
        """
            Generate a new HTTP Client with a different OAuth Resource, using the current token.

            Use this class to switch from, for example, a GraphClient to an ArmClient.
            Nullifies current cached access token, but leaves refresh token in client.

            Vars:
                - oauth_http_client_class - OAuthHTTP child class to instantiate with the current
                              class's refresh token. Note that this must be a valid
                              OAuth HTTP child class. For example, ArmClient, GraphClient,
                              or KeyVaultClient

            Returns:
                OAuthHTTPClient subclass instance
        """
        rt = self.get_current_refresh_token()
        user = User(refresh_token=rt)
        client = oauth_http_client_class(tenant=self._tenant, cred=user)
        return client

    def _set_current_token(self, token):
        """
            internal: Set the current token

            Returns:
                None
        """
        self._current_token = token

    def _ensure_access_token(self):
        """Ensure a non-expired access token is available and return it."""
        access_token = self.get_current_token()

        if access_token is None and self._auto_refresh is False:
            logging.error("cannot sent request because credential is not logged in yet."
                          "call fetchAndCacheToken first")
            raise Exception("Auto Refresh is turned off and there is no cached token")
        elif (access_token is not None
              and self._auto_refresh
              and is_token_expired( self._current_token, 600 ) ):
            # if token expires in the next 10 minutes, go get a new one and cache it locally.
            self.fetch_token()
        elif access_token is None and self._auto_refresh is True:
            self.fetch_token()

        return self.get_current_token()

    def request(self, exception_cls=None):
        """Return a fluent OAuth request builder bound to this client's session.

        Args:
            exception_cls: Optional exception type raised on unexpected status
                codes when the builder is configured to raise (via ``expect`` /
                default raise-on-error). Defaults to status-based ``AzolHTTPError``
                mapping.

        Returns:
            OAuthRequestBuilder
        """
        return OAuthRequestBuilder(
            self._session,
            ensure_token=self._ensure_access_token,
            user_agent=self._useragent,
            base_url=self._baseurl,
            default_timeout=self._request_timeout,
            exception_cls=exception_cls,
        )

    def _build_request( self, path=None, query_parameters=None, data=None, method="GET",
                        json=None, url=None, headers=None, raise_on_error=False,
                        exception_cls=None ):
        """Build an ``OAuthHTTPRequest`` without sending it."""
        if query_parameters is None:
            query_parameters = {}

        builder = (
            self.request(exception_cls=exception_cls)
            .params(query_parameters)
            .raise_on_error(raise_on_error)
        )
        if url is not None:
            builder.url(url)
        elif path is not None:
            builder.path(path)
        if data is not None:
            builder.data(data)
        if json is not None:
            builder.json(json)
        if headers is not None:
            builder.headers(headers)

        verb = getattr(builder, method.lower(), None)
        if verb is not None and method.lower() in {"get", "post", "put", "patch", "delete"}:
            return verb()
        return builder.method(method).build()

    def _send_request( self, path=None, query_parameters=None, data=None, method="GET",
                       json=None, url=None, headers=None ):
        """
            Internal method. Send request.

            Compatibility shim: does not raise on unexpected status codes so
            existing callers that inspect ``response.status_code`` keep working.
            Prefer ``self.request()`` for new code.
        """
        http_request = self._build_request(
            path=path,
            query_parameters=query_parameters,
            data=data,
            method=method,
            json=json,
            url=url,
            headers=headers,
            raise_on_error=False,
        )
        return http_request.execute()

    def get( self, path, headers=None, query_parameters=None ):
        """Make a get request .

        Args:
            - path - (string) The graph API path.
            - headers - (dict) A Dictionary of the headers to be sent in the request

        Returns:
           Request.Response object from the GET request

        """
        response = self._send_request(  path, headers=headers, query_parameters=query_parameters, method="GET" )
        return response

    def post( self, path, headers=None, json=None, query_parameters=None ):
        """Make a get request .

        Args:
            - path - (string) The graph API path.
            - headers - (dict) A Dictionary of the headers to be sent in the request

        Returns:
           Request.Response object from the GET request

        """
        response = self._send_request(  path, headers=headers, query_parameters=query_parameters, json=json, method="POST" )
        return response
