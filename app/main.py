import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from prometheus_fastapi_instrumentator import Instrumentator
from app.api.routes import users, credentials, auth
from app.api.routes import audit as audit_routes
from app.api.routes import ollama as ollama_routes

logger = structlog.get_logger()

app = FastAPI(title="User Management API", version="1.0.0", openapi_version="3.0.2")
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_headers(request: Request, call_next):
    response: Response = await call_next(request)
    path = request.url.path
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers["Content-Security-Policy"] = csp
    else:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(audit_routes.router, prefix="/audit", tags=["audit"])
app.include_router(ollama_routes.router, prefix="/ollama", tags=["ollama"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["openapi"] = "3.0.2"
    app.openapi_schema = schema
    return app.openapi_schema

setattr(app, "openapi", custom_openapi)
