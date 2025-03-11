import os
from pathlib import Path
import importlib

from fastapi import FastAPI


def get_api_versions():
    files = os.listdir(os.path.join(Path(__file__).parent.parent, "app", "api"))
    return [version for version in files if not version.startswith("_")]


def get_version_routers(version: str):
    files = os.listdir(
        os.path.join(Path(__file__).parent.parent, "app", "api", version)
    )
    return [router.split(".")[0] for router in files if not router.startswith("_")]


def add_api_versions(app: FastAPI):
    versions = get_api_versions()

    api_versions = {}
    for version in versions:
        routers = get_version_routers(version)
        version_module = f"app.api.{version}"
        api_versions[version] = FastAPI()
        for router in routers:
            _router = importlib.import_module(f"{version_module}.{router}").router
            api_versions[version].include_router(_router)

        app.mount(f"/api/{version}", api_versions[version])
