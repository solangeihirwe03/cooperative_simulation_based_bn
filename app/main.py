from fastapi import FastAPI
from app.routers import auth_routes, member_routers, admin_routes,member_contribution_routes, loan_routes, payment_routes, policy_routes, simulation_route
from fastapi.exceptions import RequestValidationError
from app.middleware.validations import validation_exception_handler,general_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
app = FastAPI()
 
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

app.include_router(member_routers.router)
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(member_contribution_routes.router)
app.include_router(loan_routes.router)
app.include_router(payment_routes.router)
app.include_router(policy_routes.router)
app.include_router(simulation_route.router)

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # allowed frontend origins
    allow_credentials=True,
    allow_methods=["*"],          # allow all methods (GET, POST, etc.)
    allow_headers=["*"], 
)
app.add_exception_handler(Exception, general_exception_handler)
@app.get("/")
def read_root():
    return RedirectResponse(url="http://localhost:8080/dashboard")