from fastapi import FastAPI

from idp_schedule_provider.authentication import routes as authentication_routes
from idp_schedule_provider.forecaster import routes as forecaster_routes

app = FastAPI()
app.include_router(authentication_routes.router)
app.include_router(forecaster_routes.router)
