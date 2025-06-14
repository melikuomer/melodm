from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel


class Settings(BaseModel):
  collection_name: Optional[str] = None

@dataclass
class IndexMetadata:
    direction: int = 1  # Default to ascending
    unique: bool = False
    name: Optional[str] = None
