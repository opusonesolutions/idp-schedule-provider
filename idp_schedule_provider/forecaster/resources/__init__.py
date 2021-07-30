import pathlib
from functools import lru_cache

resource_dir = pathlib.Path(__file__).parent.resolve()


@lru_cache()
def load_resource(key: str) -> str:
    with open(f"{resource_dir}/{key}.md") as f:
        resource = f.read()

    return resource
