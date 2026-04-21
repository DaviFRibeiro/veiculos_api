from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    marca: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cor: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    placa: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)

    # Preço armazenado em USD
    preco_usd: Mapped[float] = mapped_column(Float, nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Veiculo id={self.id} placa={self.placa} marca={self.marca}>"
