# Relatório de Melhorias e Otimizações para o Diretório `src/`

Este relatório detalha pontos de melhoria e otimização identificados no código-fonte do diretório `src/` do projeto Mech-AI. As sugestões visam aprimorar a manutenibilidade, robustez, desempenho e clareza do código.

### 1. Configuração de Logging Consistente

**Problema:** O `logging.basicConfig` é chamado em múltiplos módulos (`gemini_api_client.py`, `gemini_audio_client.py`, `chat.py`). `basicConfig` deve ser configurado apenas uma vez, idealmente no ponto de entrada da aplicação, para evitar configurações inconsistentes ou ignoradas.

**Antes:**

```python
# src/api_client/gemini_api_client.py
import logging
# ...
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# src/api_client/gemini_audio_client.py
import logging
# ...
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# src/routers/chat.py
import logging
# ...
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

**Depois:**

```python
# src/app_fastapi.py (ou um módulo de configuração de logging dedicado)
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.database import init_db_fastapi
from src.routers import services, chat

# Configurar logging uma única vez
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Obter um logger para este módulo

app = FastAPI()

# ... (restante do código)

# Em outros módulos, apenas obtenha o logger
# src/api_client/gemini_api_client.py
import logging
# ...
logger = logging.getLogger(__name__) # Obter o logger configurado

# src/api_client/gemini_audio_client.py
import logging
# ...
logger = logging.getLogger(__name__)

# src/routers/chat.py
import logging
# ...
logger = logging.getLogger(__name__)
```

### 2. Gerenciamento de Dependências do Cliente Gemini

**Problema:** O `gemini_client` é inicializado globalmente em `gemini_api_client.py` e `gemini_audio_client.py`. Isso dificulta testes (mocking) e pode levar a problemas em ambientes com diferentes configurações ou em aplicações maiores.

**Antes:**

```python
# src/api_client/gemini_api_client.py
from google import genai
from src.core.config import Config

gemini_client = None
if Config.GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)

async def process_user_message(message):
    if not gemini_client:
        return None, "API Key do Gemini não configurada"
    # ...
```

**Depois:**

```python
# src/api_client/gemini_api_client.py
from google import genai
from src.core.config import Config
from google.genai import types

class GeminiAPIClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não configurada.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = Config.GEMINI_MODEL # Ou passe como parâmetro

    async def process_user_message(self, message: str):
        # ... use self.client e self.model_name
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config=generation_config
        )
        # ...

# src/routers/chat.py (exemplo de como injetar a dependência)
from fastapi import APIRouter, Depends
from src.api_client.gemini_api_client import GeminiAPIClient
from src.core.config import Config

router = APIRouter()

def get_gemini_api_client():
    return GeminiAPIClient(api_key=Config.GEMINI_API_KEY)

@router.post("/api/chat", response_model=ChatResponse)
async def chat_api(
    chat_message: ChatMessage,
    db: AsyncSession = Depends(get_db),
    gemini_client: GeminiAPIClient = Depends(get_gemini_api_client) # Injeção
):
    # ... use gemini_client.process_user_message
```

### 3. Tratamento de Exceções Mais Específico

**Problema:** Em `gemini_api_client.py` e `gemini_audio_client.py`, exceções genéricas (`Exception`) são capturadas. Isso pode mascarar erros inesperados e dificultar a depuração. É preferível capturar exceções mais específicas.

**Antes:**

```python
# src/api_client/gemini_api_client.py
    except Exception as e:
        logging.error(f"Error processing Gemini response: {e}")
        return None, str(e)
```

**Depois:**

```python
# src/api_client/gemini_api_client.py
from google.api_core.exceptions import GoogleAPIError # Exemplo de exceção específica

    except GoogleAPIError as e:
        logging.error(f"Gemini API error: {e}")
        return None, f"Erro na API do Gemini: {str(e)}"
    except ValueError as e: # Para erros de validação, por exemplo
        logging.error(f"Validation error: {e}")
        return None, f"Erro de validação: {str(e)}"
    except Exception as e: # Captura genérica como último recurso
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return None, f"Ocorreu um erro inesperado: {str(e)}"
```

### 4. Externalização de Prompts do Gemini

**Problema:** O prompt do Gemini em `gemini_api_client.py` é uma string grande e hardcoded. Para prompts mais complexos ou que precisam de ajustes frequentes, externalizá-los ou usar um sistema de templates pode ser benéfico.

**Antes:**

```python
# src/api_client/gemini_api_client.py
    full_prompt = f"""Você deve classificar a intenção do mecânico e extrair os dados.
# ... (muitas linhas)
IMPORTANTE: Use APENAS "record_service" ou "search_service" como intent."""
```

**Depois (Exemplo com arquivo de template ou constante):**

```python
# src/utils/prompts.py
GEMINI_CLASSIFICATION_PROMPT = """Você deve classificar a intenção do mecânico e extrair os dados.

INTENTS PERMITIDOS (use EXATAMENTE um destes):
- "record_service": quando o mecânico quer REGISTRAR/CRIAR um novo serviço
- "search_service": quando o mecânico quer BUSCAR/CONSULTAR serviços existentes
- "list_active_services": quando o mecânico quer LISTAR todos os serviços ativos

Ao extrair a marca e o modelo do carro, seja o mais preciso possível. Se a marca não for explicitamente mencionada, tente inferir a marca com base no modelo. Por exemplo:
- "BMW 320i" deve ter "BMW" como marca e "320i" como modelo.
- "Corolla" deve ter "Toyota" como marca e "Corolla" como modelo.

MENSAGEM DO MECÂNICO: {message}

IMPORTANTE: Use APENAS "record_service" ou "search_service" como intent."""

# src/api_client/gemini_api_client.py
from src.utils.prompts import GEMINI_CLASSIFICATION_PROMPT

async def process_user_message(message):
    # ...
    full_prompt = GEMINI_CLASSIFICATION_PROMPT.format(message=message)
    # ...
```

### 5. Uso Consistente de Modelos Pydantic para Respostas da API

**Problema:** Em `src/routers/services.py`, alguns endpoints retornam diretamente objetos SQLAlchemy (`db_client`, `db_car`, `db_service_record`) após a criação, embora modelos Pydantic de resposta (`ClientResponse`, `CarResponse`, `ServiceRecordResponse`) estejam definidos. É uma boa prática usar os modelos Pydantic para todas as respostas da API para garantir consistência, validação e documentação automática.

**Antes:**

```python
# src/routers/services.py
@router.post("/api/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_db)):
    db_client = Client(**client_data.model_dump())
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client # Retorna o objeto SQLAlchemy diretamente
```

**Depois:**

```python
# src/routers/services.py
@router.post("/api/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreate, db: AsyncSession = Depends(get_db)):
    db_client = Client(**client_data.model_dump())
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return ClientResponse.model_validate(db_client) # Valida e retorna o modelo Pydantic
```

### 6. Tratamento de Datas e Fusos Horários

**Problema:** Em `src/services/service_management.py`, a conversão de string para data (`datetime.strptime`) não considera fusos horários, e `datetime.now().date()` usa a data local sem fuso horário explícito. Isso pode levar a inconsistências em sistemas distribuídos ou quando o servidor está em um fuso horário diferente do esperado.

**Antes:**

```python
# src/services/service_management.py
        service_date = None
        if service_date_str:
            try:
                service_date = datetime.strptime(service_date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Could not parse date '{service_date_str}'. Using current date.")
                pass
        
        record = await self.service_repo.create_service_record(
            # ...
            date=service_date or datetime.now().date(),
            # ...
        )
```

**Depois:**

```python
# src/services/service_management.py
from datetime import datetime, date, timezone

        service_date: date = None
        if service_date_str:
            try:
                # Parse a data e converte para UTC se necessário, ou assume que a string já é UTC
                # Para simplicidade, vamos apenas parsear a data sem hora
                service_date = datetime.strptime(service_date_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Could not parse date '{service_date_str}'. Using current UTC date.")
                pass
        
        record = await self.service_repo.create_service_record(
            # ...
            date=service_date or datetime.now(timezone.utc).date(), # Usar data UTC
            # ...
        )
```

### 7. Otimização de String Formatting em `_format_service_records_for_response`

**Problema:** Em `src/services/chat_service.py`, o método `_format_service_records_for_response` usa `append` em uma lista e depois `join`, o que é bom. No entanto, a formatação das strings pode ser um pouco mais concisa.

**Antes:**

```python
# src/services/chat_service.py
    def _format_service_records_for_response(self, records: list) -> str:
        formatted_strings = []
        for i, record in enumerate(records):
            client_name = record.car.owner.name if record.car and record.car.owner else "Desconhecido"
            car_info = f"{record.car.brand} {record.car.model}" if record.car else "Carro Desconhecido"
            service_desc = record.servico
            service_date = record.date.strftime('%Y-%m-%d') if record.date else "Data Desconhecida"

            formatted_strings.append(f"**Cliente:** {client_name}
"
                f"&emsp;**Carro:** {car_info}
"
                f"&emsp;**Serviço:** {service_desc}
"
                f"&emsp;**Data:** {service_date}
"
                "───────────────────"
            )
        return "
".join(formatted_strings)
```

**Depois:**

```python
# src/services/chat_service.py
    def _format_service_records_for_response(self, records: list) -> str:
        formatted_strings = []
        for record in records:
            client_name = record.car.owner.name if record.car and record.car.owner else "Desconhecido"
            car_info = f"{record.car.brand or ''} {record.car.model or ''}".strip() or "Carro Desconhecido"
            service_date = record.date.strftime('%Y-%m-%d') if record.date else "Data Desconhecida"

            formatted_strings.append(
                f"**Cliente:** {client_name}
"
                f"&emsp;**Carro:** {car_info}
"
                f"&emsp;**Serviço:** {record.servico}
"
                f"&emsp;**Data:** {service_date}
"
                "───────────────────"
            )
        return "
".join(formatted_strings)
```

### 8. Refatoração de `_process_and_handle_intent` em `src/routers/chat.py`

**Problema:** A função `_process_and_handle_intent` em `src/routers/chat.py` duplica a lógica de tratamento de erros HTTP para a API do Gemini.

**Antes:**

```python
# src/routers/chat.py
async def _process_and_handle_intent(message: str, db: AsyncSession) -> ChatResponse:
    # ...
    gemini_response, error = await process_user_message(message)
    # ...
    if error:
        logging.error(f"Gemini API error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error)
    # ...
```

**Depois (assumindo que `process_user_message` levanta exceções):**

```python
# src/api_client/gemini_api_client.py (modificado para levantar exceções)
async def process_user_message(message):
    if not gemini_client:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API Key do Gemini não configurada")
    try:
        # ...
        return parsed_response
    except Exception as e:
        logging.error(f"Error processing Gemini response: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro na API do Gemini: {str(e)}")

# src/routers/chat.py
async def _process_and_handle_intent(message: str, db: AsyncSession) -> ChatResponse:
    if not message:
        logging.warning("Message to process is empty.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A mensagem processada está vazia.")

    # Agora process_user_message levanta HTTPException diretamente
    gemini_response = await process_user_message(message)
    logging.debug(f"Gemini API raw response: {json.dumps(gemini_response)}")

    chat_service = ChatService(db)
    return await chat_service.handle_intent(gemini_response)
```

### 9. Uso de `model_validate` para Pydantic Models

**Problema:** Em `src/services/chat_service.py`, ao criar `ServiceDataResponse` a partir de um objeto SQLAlchemy, `ServiceDataResponse.model_validate(service_result["service_record"])` é usado, o que é correto. No entanto, em `src/routers/services.py`, o retorno direto de objetos SQLAlchemy para `response_model` pode ser inconsistente. A sugestão 5 já aborda isso, mas é importante reforçar o uso de `model_validate` ou `model_dump` para garantir que os dados estejam no formato Pydantic esperado.

### 10. `Config.GEMINI_MODEL` em `gemini_audio_client.py`

**Problema:** Em `src/api_client/gemini_audio_client.py`, o modelo `gemini-2.5-flash` é hardcoded. Seria melhor usar `Config.GEMINI_MODEL` para consistência.

**Antes:**

```python
# src/api_client/gemini_audio_client.py
        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=generate_content_config
        )
```

**Depois:**

```python
# src/api_client/gemini_audio_client.py
from src.core.config import Config

        response = await gemini_client.aio.models.generate_content(
            model=Config.GEMINI_MODEL, # Usar a configuração
            contents=contents,
            config=generate_content_config
        )
```

Este relatório abrange as principais áreas de melhoria identificadas. A implementação dessas sugestões contribuirá para um código mais robusto, manutenível e eficiente.