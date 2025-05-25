from dataclasses import dataclass

from src.database import DARPServer


@dataclass
class ToolInfo:
    tool_name: str
    server: DARPServer
