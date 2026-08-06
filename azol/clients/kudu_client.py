"""A module containing a client for interacting with the Kudu API.
"""
from html.parser import HTMLParser

from azol.clients.oauth_http_client import OAuthHTTPClient
from azol.constants import OAuthResourceIDs
from azol.http import HttpCall


class SCMEnvVarHTMLParser(HTMLParser):

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self._env_variables = {}
        self.new_data=''

    def get_env_variables(self):
        return self._env_variables

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.new_data=''

    def handle_endtag(self, tag):
        if tag == "li":
            key, val = self.new_data.split( " = " )
            self._env_variables[key] = val
            self.new_data=''

    def handle_data(self, data):
        self.new_data = data


class KuduClient( OAuthHTTPClient ):
    """
        An HTTP client for interacting with the App Service Kudu resource
    """
    
    def __init__( self, scm_url, *args, **kwargs ):
        super().__init__( oauth_resource=OAuthResourceIDs.Arm, base_url=scm_url, *args, **kwargs)

    def call(self, path: str) -> HttpCall:
        """Return a fluent Kudu/SCM call bound to this client.

        Failures raise ``AzolHTTPError`` (or a status-specific subclass).
        """
        return HttpCall(self, path, next_link_key=None)

    def get_env_variables(self):
        response = self.call("/Env").get().response
        
        # Get the index of the beginning of the environment variables in HTML
        content = str(response.content)
        start_index_value = "<h3 id=\"envVariables\">Environment variables</h3>"
        start_index = content.index(start_index_value) + len(start_index_value)
        end_index_value = "<h3 id=\"path\">PATH</h3>"
        end_index = content.index(end_index_value)

        env_variable_html_content=content[start_index:end_index]

        parser = SCMEnvVarHTMLParser()
        parser.feed(env_variable_html_content)

        return parser.get_env_variables()

    def get_processes(self):
        return self.call("/api/processes").get().json()

    def get_process(self, pid):
        return self.call(f"/api/processes/{pid}").get().json()

    def get_process_dump(self, pid):
        return self.call(f"/api/processes/{pid}/dump").get().content

    def ls(self, path):
        return self.call(f"/api/vfs/{path}").get().json()

    def get_file(self, path):
        return self.call(f"/api/vfs/{path}").get().content

    def command( self, command, directory=None ):
        """Execute a command via the Kudu API.
        
        Returns:
            A dict containing the results of the command

        Raises:
            AzolHTTPError: An error occurred accessing the Kudu API
        """
        body={
            "command":command
        }
        if directory is not None:
            body["dir"]=directory
        return self.call("/api/command").body(body).post().json()
    
    def get_settings( self ):
        """Get settings
        
        Returns:
            A dict containing the settings

        Raises:
            AzolHTTPError: An error occurred accessing the Kudu API
        """
        return self.call("/api/settings").get().json()
    
    def get_setting( self, setting ):
        """Get setting
        
        Returns:
            Raw setting content

        Raises:
            AzolHTTPError: An error occurred accessing the Kudu API
        """
        return self.call(f"/api/settings/{setting}").get().content
