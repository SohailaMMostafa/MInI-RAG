from enum import Enum

class VDBEnums(Enum):
    QDRANT = "QDRANT"

class Distance(Enum):
    COSINE = "cosine"
    DOT = "dot"