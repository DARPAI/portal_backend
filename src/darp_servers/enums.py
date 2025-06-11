from enum import StrEnum


class DARPServerTransportProtocol(StrEnum):
    STREAMABLE_HTTP = "STREAMBLE_HTTP"
    SSE = "SSE"
