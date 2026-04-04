from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas import policy
from app.services import policy_service
from app.dependencies import require_role

router = APIRouter(prefix="/policies", tags=["policies"])

@router.post("/", response_model=policy.PolicyResponse)
def create_policy(
    policy_data: policy.PolicyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only: Create a new policy"""
    return policy_service.create_policy(db, policy_data)

@router.get("/", response_model=List[policy.PolicyResponse])
def get_all_policies(
    db: Session = Depends(get_db)
):
    """Fetch all policies"""
    return policy_service.get_all_policies(db)

@router.get("/{policy_id}", response_model=policy.PolicyResponse)
def get_single_policy(
    policy_id: int,
    db: Session = Depends(get_db)
):
    """Fetch a specific policy by ID"""
    return policy_service.get_policy(db, policy_id)

@router.patch("/{policy_id}", response_model=policy.PolicyResponse)
def update_policy(
    policy_id: int,
    policy_update: policy.PolicyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only: Update policy details"""
    return policy_service.update_policy(db, policy_id, policy_update)

@router.patch("/{policy_id}/status", response_model=policy.PolicyResponse)
def update_policy_status(
    policy_id: int,
    status_update: policy.PolicyStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only: Activate or deactivate a policy. Activating auto-deactivates others."""
    return policy_service.update_policy_status(db, policy_id, status_update)
