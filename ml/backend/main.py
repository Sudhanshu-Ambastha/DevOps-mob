from fastapi import FastAPI
from routes.problem_routes import router as problem_router

app = FastAPI(title="DevBridge Modular Backend")
app.include_router(problem_router)