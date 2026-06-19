import pathlib

# Resolve the path to the actual application package located in backend/app
_root = pathlib.Path(__file__).resolve().parent.parent
_backend_app = _root / "backend" / "app"

# If the backend/app directory exists, add it to this package's __path__ so submodules can be found.
if _backend_app.is_dir():
    __path__.append(str(_backend_app))
