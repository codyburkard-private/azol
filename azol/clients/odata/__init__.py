"""OData / Graph call primitives for Graph clients."""
from azol.clients.odata.builder import ODataQueryBuilder
from azol.clients.odata.call import GraphCall
from azol.clients.odata.request import ODataHTTPRequest
from azol.clients.odata.result import GraphResult, ODataResponse

__all__ = [
    "GraphCall",
    "GraphResult",
    "ODataQueryBuilder",
    "ODataHTTPRequest",
    "ODataResponse",
]
