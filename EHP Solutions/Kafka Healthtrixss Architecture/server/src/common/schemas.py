from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MembershipRecord:
    id: int
    first_name: str
    last_name: str
    birth_date: datetime
