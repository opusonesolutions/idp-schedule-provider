import io
import json

from idp_schedule_provider.main import app


def create_docs():
    with io.open("public/apispec.json", 'w') as writer:
        json.dump(app.openapi(), writer)
