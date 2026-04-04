from sqlalchemy.orm import Session
from app.models.policies import Policy
from app.enums.policies import PolicyStatus
from app.schemas.policy import PolicyCreate, PolicyUpdate, PolicyStatusUpdate
from fastapi import HTTPException

def enforce_single_active_policy(db: Session, active_policy_id: int):
    # Deactivate all other policies
    db.query(Policy).filter(Policy.policy_id != active_policy_id, Policy.status == PolicyStatus.active).update({"status": PolicyStatus.inactive})
    db.commit()

def create_policy(db: Session, policy_data: PolicyCreate):
    new_policy = Policy(
        policy_name=policy_data.policy_name,
        interest_rate=policy_data.interest_rate,
        max_loan_amount=policy_data.max_loan_amount,
        repayment_period=policy_data.repayment_period,
        penalty_rate=policy_data.penalty_rate
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return new_policy

def get_all_policies(db: Session):
    return db.query(Policy).all()

def get_policy(db: Session, policy_id: int):
    policy = db.query(Policy).filter(Policy.policy_id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

def update_policy(db: Session, policy_id: int, policy_update: PolicyUpdate):
    policy = get_policy(db, policy_id)
    
    update_data = policy_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(policy, key, value)
        
    db.commit()
    db.refresh(policy)
    return policy

def update_policy_status(db: Session, policy_id: int, status_update: PolicyStatusUpdate):
    policy = get_policy(db, policy_id)
    policy.status = status_update.status
    db.commit()
    db.refresh(policy)
    
    if policy.status == PolicyStatus.active:
        enforce_single_active_policy(db, policy.policy_id)
        
    return policy
