from dataclasses import dataclass, field
from sugarcane.core.helpers import json_response


@dataclass
class NodeResponse:
    status: bool = False
    data: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    etag: str = ""

    def json_response(self):
        return json_response(data=self.data, headers=self.headers, etag=self.etag)


@dataclass
class EmptyNodeResponse(NodeResponse):
    status: bool = field(default=False)
