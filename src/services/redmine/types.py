from dataclasses import dataclass
from typing import Optional


@dataclass
class CustomProject:
    """Custom Redmine project with ID and name"""

    id: int = 0
    name: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.id} - {self.name}"
