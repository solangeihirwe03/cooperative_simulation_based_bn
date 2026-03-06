from fastapi import FastAPI
from app.routers import member_routers
 
app = FastAPI()
 
app.include_router(member_routers.router)
@app.get("/")
def read_root():
    return {"message" : "Welcome to the simulation based decision support for cooperative policy planning!"}