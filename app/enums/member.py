from enum import Enum

class MemberStatus(str,Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class MemberRole(str, Enum):
    MEMBER="member"
    ADMIN="admin"