from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class VeiculoBase(BaseModel):
    marca: str = Field(..., min_length=1, max_length=100, examples=["Toyota"])
    modelo: str = Field(..., min_length=1, max_length=100, examples=["Corolla"])
    ano: int = Field(..., ge=1886, le=2100, examples=[2023])
    cor: str = Field(..., min_length=1, max_length=50, examples=["Prata"])
    placa: str = Field(..., min_length=7, max_length=10, examples=["ABC1D23"])

    @field_validator("placa")
    @classmethod
    def placa_upper(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("marca", "modelo", "cor")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()


class VeiculoCreate(VeiculoBase):
    """Payload para criar um veículo. Preço informado em BRL; convertido para USD internamente."""
    preco_brl: float = Field(..., gt=0, examples=[85000.00], description="Preço em Reais (BRL)")


class VeiculoUpdate(BaseModel):
    """PUT: todos os campos obrigatórios."""
    marca: str = Field(..., min_length=1, max_length=100)
    modelo: str = Field(..., min_length=1, max_length=100)
    ano: int = Field(..., ge=1886, le=2100)
    cor: str = Field(..., min_length=1, max_length=50)
    placa: str = Field(..., min_length=7, max_length=10)
    preco_brl: float = Field(..., gt=0)

    @field_validator("placa")
    @classmethod
    def placa_upper(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("marca", "modelo", "cor")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()


class VeiculoPatch(BaseModel):
    """PATCH: todos os campos opcionais."""
    marca: Optional[str] = Field(None, min_length=1, max_length=100)
    modelo: Optional[str] = Field(None, min_length=1, max_length=100)
    ano: Optional[int] = Field(None, ge=1886, le=2100)
    cor: Optional[str] = Field(None, min_length=1, max_length=50)
    placa: Optional[str] = Field(None, min_length=7, max_length=10)
    preco_brl: Optional[float] = Field(None, gt=0)

    @field_validator("placa")
    @classmethod
    def placa_upper(cls, v: Optional[str]) -> Optional[str]:
        return v.upper().strip() if v else v

    @field_validator("marca", "modelo", "cor")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else v


class VeiculoResponse(VeiculoBase):
    id: int
    preco_usd: float
    preco_brl: Optional[float] = None
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class VeiculoListResponse(BaseModel):
    items: list[VeiculoResponse]
    total: int
    page: int
    size: int
    pages: int


class RelatorioMarcaItem(BaseModel):
    marca: str
    total: int


class RelatorioMarcaResponse(BaseModel):
    items: list[RelatorioMarcaItem]
    total_marcas: int
    total_veiculos: int
