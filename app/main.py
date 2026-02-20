from fastapi import FastAPI
from app.database.database import connect
 
app = FastAPI()
connection = connect()
 
@app.get("/")
def read_root():
    return {"message" : "Welcome to the simulation based decision support for cooperative policy planning!"}