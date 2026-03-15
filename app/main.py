from fastapi import FastAPI
from app.routers import auth_routes, member_routers, admin_routes
from fastapi.exceptions import RequestValidationError
from app.middleware.validations import validation_exception_handler,general_exception_handler
 
app = FastAPI()
 
app.include_router(member_routers.router)
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_exception_handler(Exception, general_exception_handler)
@app.get("/")
def read_root():
    return {"message" : "Welcome to the simulation based decision support for cooperative policy planning!"}