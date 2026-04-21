from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.cache import close_redis
from app.core.database import create_tables
from app.routers import auth, relatorios, veiculos


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield
    await close_redis()


app = FastAPI(
    title="Veículos API",
    description=(
        "API REST para gerenciamento de veículos com controle de acesso baseado em perfis.\n\n"
        "## Autenticação\n"
        "Use `POST /auth/token` para obter um Bearer token.\n\n"
        "**Usuários de teste:**\n"
        "- `admin` / `admin123` → ADMIN (acesso total)\n"
        "- `user` / `user123` → USER (somente leitura)\n\n"
        "## Preços\n"
        "Preços são enviados em BRL e armazenados em USD usando cotação em tempo real."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "Tinnova Challenge"},
    license_info={"name": "MIT"},
)


# ── Standardised error responses ────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "campo": " → ".join(str(loc) for loc in error["loc"]),
            "mensagem": error["msg"],
            "tipo": error["type"],
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"erro": "Dados inválidos", "detalhes": errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"erro": "Erro interno no servidor", "detalhe": str(exc)},
    )


# ── Routers ──────────────────────────────────────────────────────────────────
# relatorios must be registered before veiculos to avoid route shadowing
app.include_router(auth.router)
app.include_router(relatorios.router)
app.include_router(veiculos.router)


@app.get("/", tags=["Health"], summary="Health check")
async def root():
    return {"status": "ok", "docs": "/docs"}
