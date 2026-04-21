from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import authenticate_user, create_access_token
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/token",
    response_model=Token,
    summary="Obter token JWT",
    description=(
        "Autentica com usuário e senha, retorna Bearer token.\n\n"
        "**Usuários de teste:**\n"
        "- `admin` / `admin123` → perfil ADMIN (acesso total)\n"
        "- `user` / `user123` → perfil USER (somente leitura)"
    ),
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return Token(access_token=token)
