from  fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas import policy
from app.services import simulation_engine
from app.dependencies import require_role

router = APIRouter(prefix="/simulation", tags=["simulation"])

@router.post("/run", response_model=dict)
def run_simulation(
    simulation_data: policy.PolicySimulationCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("admin"))
):
    """Admin-only endpoint to run a simulation based on provided policy parameters"""
    
    data = simulation_engine.get_cooperativer_metrics(db, current_user.cooperative_id)
    print("Data for Simulation:", data)
    
    # Get cooperative metrics and run the simulation
    return simulation_engine.run_simulation(simulation_data, data)