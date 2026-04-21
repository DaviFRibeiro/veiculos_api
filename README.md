# Veículos API

API REST para gerenciamento de veículos com autenticação JWT, controle de acesso por perfis, conversão de preços USD/BRL em tempo real e cache Redis.

## Tecnologias

- **FastAPI** — framework web assíncrono
- **SQLAlchemy 2 (async)** — ORM com suporte a asyncpg
- **PostgreSQL** — banco de dados principal
- **Redis** — cache da cotação USD/BRL
- **JWT (jose)** — autenticação e autorização
- **Pydantic v2** — validação de schemas
- **pytest + pytest-asyncio** — testes automatizados (≥60% de cobertura)

---

## Execução com Docker (recomendado)

```bash
# Clone e entre na pasta
git clone https://github.com/DaviFRibeiro/veiculos_api.git
cd veiculos-api

# Suba os serviços (PostgreSQL + Redis + API)
docker-compose up --build
```

A API estará disponível em: http://localhost:8000  
Documentação Swagger: http://localhost:8000/docs

---

## Execução local

### Pré-requisitos

- Python 3.12+
- PostgreSQL rodando
- Redis rodando

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/DaviFRibeiro/veiculos_api.git
cd veiculos-api

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais de DB e Redis

# 5. Execute a aplicação
uvicorn app.main:app --reload
```

As tabelas são criadas automaticamente no startup (`lifespan`).

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL async do banco |
| `DATABASE_URL_SYNC` | `postgresql://...` | URL sync (Alembic) |
| `REDIS_URL` | `redis://localhost:6379/0` | URL do Redis |
| `SECRET_KEY` | — | Chave secreta JWT (troque em produção) |
| `ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Expiração do token |
| `USD_CACHE_TTL` | `3600` | TTL do cache da cotação (segundos) |

---

## Autenticação

A API usa **Bearer Token JWT**. Obtenha o token em `POST /auth/token`.

### Usuários de teste

| Usuário | Senha | Perfil | Permissões |
|---|---|---|---|
| `admin` | `admin123` | ADMIN | GET + POST + PUT + PATCH + DELETE |
| `user` | `user123` | USER | Somente GET |

### Exemplo com curl

```bash
# Obter token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin123" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq -r .access_token)

# Criar veículo
curl -X POST http://localhost:8000/veiculos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"marca":"Toyota","modelo":"Corolla","ano":2022,"cor":"Prata","placa":"ABC1D23","preco_brl":120000}'

# Listar veículos
curl http://localhost:8000/veiculos \
  -H "Authorization: Bearer $TOKEN"
```

---

## Endpoints

### Autenticação
| Método | Endpoint | Descrição |
|---|---|---|
| POST | `/auth/token` | Obter token JWT |

### Veículos
| Método | Endpoint | Perfil | Descrição |
|---|---|---|---|
| GET | `/veiculos` | USER/ADMIN | Listar com filtros e paginação |
| GET | `/veiculos/{id}` | USER/ADMIN | Detalhar veículo |
| POST | `/veiculos` | ADMIN | Criar veículo |
| PUT | `/veiculos/{id}` | ADMIN | Atualizar completamente |
| PATCH | `/veiculos/{id}` | ADMIN | Atualizar parcialmente |
| DELETE | `/veiculos/{id}` | ADMIN | Soft delete |

### Relatórios
| Método | Endpoint | Perfil | Descrição |
|---|---|---|---|
| GET | `/veiculos/relatorios/por-marca` | USER/ADMIN | Veículos agrupados por marca |

### Filtros disponíveis em `GET /veiculos`

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `marca` | string | Filtro parcial (case-insensitive) |
| `ano` | int | Ano exato |
| `cor` | string | Filtro parcial (case-insensitive) |
| `minPreco` | float | Preço mínimo em BRL |
| `maxPreco` | float | Preço máximo em BRL |
| `page` | int | Página (padrão: 1) |
| `size` | int | Itens por página (padrão: 20, máx: 100) |
| `order_by` | string | Campo de ordenação |
| `order_dir` | asc/desc | Direção da ordenação |

---

## Preços

- O preço é **enviado em BRL** pelo cliente e **armazenado em USD** internamente.
- A cotação USD/BRL é obtida da [AwesomeAPI](https://economia.awesomeapi.com.br/json/last/USD-BRL).
- Em caso de falha, usa [Frankfurter](https://api.frankfurter.app/latest?from=USD&to=BRL) como fallback.
- A cotação é **cacheada no Redis** por 1 hora (configurável via `USD_CACHE_TTL`).
- As respostas incluem tanto `preco_usd` quanto `preco_brl` (convertido na hora da consulta).

---

## Testes

```bash
# Instalar dependências de teste
pip install -r requirements.txt

# Executar todos os testes com cobertura
pytest

# Executar apenas testes unitários
pytest tests/unit/ -v

# Executar apenas testes de integração
pytest tests/integration/ -v

# Executar testes e2e
pytest tests/e2e/ -v

# Ver relatório HTML de cobertura
open htmlcov/index.html
```

Os testes usam **SQLite in-memory** e mocks para Redis e APIs externas — nenhuma dependência externa é necessária para rodar os testes.

### Cobertura esperada (Pleno ≥ 60%)

| Categoria | Testes |
|---|---|
| Unit - Services | Duplicidade de placa, filtros combinados, PUT/PATCH inválido |
| Unit - Câmbio | Cache Redis, fallback Frankfurter, falha total |
| Integration - Auth | 401/403/409, perfis USER/ADMIN |
| Integration - CRUD | Todos os endpoints, paginação, soft delete |
| E2E | Fluxo completo admin, fluxo user somente leitura, unicidade de placa |

---

## Estrutura do projeto

```
veiculos-api/
├── app/
│   ├── main.py                    # FastAPI app, lifespan, error handlers
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── database.py            # SQLAlchemy async engine + session
│   │   ├── security.py            # JWT, bcrypt, get_current_user, require_admin
│   │   └── cache.py               # Redis + cotação USD/BRL com fallback
│   ├── models/
│   │   └── veiculo.py             # ORM model (soft delete com ativo=False)
│   ├── schemas/
│   │   ├── veiculo.py             # Pydantic: Create/Update/Patch/Response
│   │   └── auth.py                # Token schema
│   ├── repositories/
│   │   └── veiculo_repo.py        # Queries SQL, filtros, paginação
│   ├── services/
│   │   ├── veiculo_service.py     # Regras de negócio
│   │   └── cambio_service.py      # Conversão BRL/USD
│   └── routers/
│       ├── auth.py                # POST /auth/token
│       ├── veiculos.py            # CRUD endpoints
│       └── relatorios.py          # GET /relatorios/por-marca
├── tests/
│   ├── conftest.py                # Fixtures: db, client, tokens
│   ├── unit/
│   │   ├── test_veiculo_service.py
│   │   └── test_cambio_service.py
│   ├── integration/
│   │   ├── test_auth.py
│   │   └── test_veiculos_router.py
│   └── e2e/
│       └── test_fluxo_completo.py
├── docker-compose.yml
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── .env.example
```
