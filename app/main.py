from fastapi import FastAPI
from app.routers import member_routers,admin_routes
 
app = FastAPI()
 
app.include_router(member_routers.router)
app.include_router(admin_routes.router)
@app.get("/")
def read_root():
    return {"message" : "Welcome to the simulation based decision support for cooperative policy planning!"}