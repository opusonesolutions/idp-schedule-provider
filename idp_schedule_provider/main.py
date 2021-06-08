from fastapi import FastAPI
from pydantic import BaseModel

from idp_schedule_provider.authentication import routes as authentication_routes
from idp_schedule_provider.forecaster import routes as forecaster_routes

app = FastAPI(
    title="IDP Schedule Provider",
    description="A reference implementation of a provider for the IDP external schedule interface",
)
app.include_router(authentication_routes.router)
app.include_router(forecaster_routes.router)


class AboutResponseModel(BaseModel):
    title: str
    description: str
    docs_url: str


@app.get("/", response_model=AboutResponseModel)
async def about():
    return AboutResponseModel(title=app.title, description=app.description, docs_url=app.docs_url)
