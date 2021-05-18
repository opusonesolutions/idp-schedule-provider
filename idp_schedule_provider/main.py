import json

from fastapi import FastAPI, Response
from fastapi.exceptions import RequestValidationError

from idp_schedule_provider import routes

app = FastAPI()
app.include_router(routes.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return Response(json.dumps(exc.errors()), 400)
