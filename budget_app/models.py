from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Category:
    name: str

@dataclass
class Budget:
    month: str
    amount: int

@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: Optional[str] = None
    tags: Optional[List[str]] = field(default_factory=list)