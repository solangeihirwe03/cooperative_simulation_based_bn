from enum import Enum

class LoanStatus(str,Enum):
    pending = "pending"
    approved = "approved"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"