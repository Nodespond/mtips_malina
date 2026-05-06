from dataclasses import dataclass
from typing import Union, Optional, Set

@dataclass
class Property:
    id: int
    name: str
    type: str

@dataclass
class VarietyValue:
    categorical_value: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None