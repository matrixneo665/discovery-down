
from dataclasses import dataclass
from typing import Optional

@dataclass
class WidevineArgs:
    pssh: str
    url: str
    preAuthToken: str
    verbose: Optional[bool]
    headers: dict
    cache: bool
    auth: str
    buildinfo: Optional[str] = ""