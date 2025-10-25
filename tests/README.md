# Testes - Mech AI

Este diretório contém os testes unitários e de integração para o projeto Mech AI, com foco especial nos clientes da API Gemini.

## Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py                           # Configurações compartilhadas
├── README.md                             # Esta documentação
├── unit/                                 # Testes unitários
│   ├── __init__.py
│   ├── test_gemini_api_client.py        # Testes para process_user_message
│   └── test_gemini_audio_client.py      # Testes para transcribe_audio
└── integration/                          # Testes de integração
    ├── __init__.py
    └── test_api_client_integration.py   # Testes de fluxo completo
```

## Instalação das Dependências

Instale as dependências de teste:

```bash
pip install -r requirements.txt
```

As seguintes bibliotecas de teste serão instaladas:
- `pytest` - Framework de testes
- `pytest-asyncio` - Suporte para testes assíncronos
- `pytest-mock` - Utilitários para mocking
- `pytest-cov` - Cobertura de código
- `httpx` - Cliente HTTP para testes de API

## Executando os Testes

### Executar todos os testes

```bash
pytest
```

### Executar apenas testes unitários

```bash
pytest tests/unit/
```

ou usando marcadores:

```bash
pytest -m unit
```

### Executar apenas testes de integração

```bash
pytest tests/integration/
```

ou usando marcadores:

```bash
pytest -m integration
```

### Executar testes de um arquivo específico

```bash
pytest tests/unit/test_gemini_api_client.py
```

### Executar um teste específico

```bash
pytest tests/unit/test_gemini_api_client.py::TestProcessUserMessage::test_process_message_without_api_key
```

### Executar com verbose

```bash
pytest -v
```

### Executar com cobertura de código

```bash
pytest --cov=src/api_client --cov-report=html
```

Isso gerará um relatório HTML em `htmlcov/index.html`.

### Executar testes em paralelo (mais rápido)

```bash
pip install pytest-xdist
pytest -n auto
```

## Cobertura de Testes

Os testes cobrem os seguintes módulos:

### `src/api_client/gemini_api_client.py`

**Função testada:** `process_user_message(message)`

**Testes unitários:**
- ✅ Validação de API key ausente
- ✅ Processamento bem-sucedido de intent `record_service`
- ✅ Processamento bem-sucedido de intent `search_service`
- ✅ Tratamento de erros da API
- ✅ Validação do prompt gerado
- ✅ Validação dos parâmetros de configuração
- ✅ Processamento de mensagem vazia
- ✅ Processamento de mensagem com caracteres especiais

### `src/api_client/gemini_audio_client.py`

**Função testada:** `transcribe_audio(audio_file)`

**Testes unitários:**
- ✅ Validação de API key ausente
- ✅ Transcrição bem-sucedida
- ✅ Erro com arquivo vazio
- ✅ Tratamento de erros da API
- ✅ Transcrição que retorna texto vazio
- ✅ Validação dos parâmetros enviados
- ✅ Suporte a diferentes tipos MIME
- ✅ Fallback quando content_type é None
- ✅ Processamento de arquivos grandes
- ✅ Validação dos parâmetros de configuração
- ✅ Remoção de espaços em branco
- ✅ Processamento de caracteres especiais

### Testes de Integração

**Fluxos testados:**
- ✅ Fluxo completo de registro de serviço
- ✅ Fluxo completo de busca de serviço
- ✅ Fluxo áudio → transcrição → processamento → registro
- ✅ Validação de API key em múltiplos módulos
- ✅ Propagação de erros ao longo do pipeline
- ✅ Validação de schemas (completo, mínimo, busca)
- ✅ Uso de configurações customizadas
- ✅ Requisições concorrentes (transcrições e processamentos)

## Estrutura dos Testes

### Testes Unitários

Os testes unitários focam em testar funções individuais isoladamente, usando mocks para simular dependências externas (API Gemini, configurações, etc.).

**Características:**
- Rápidos (< 1s por teste)
- Isolados (não dependem de recursos externos)
- Testam casos específicos e edge cases
- Usam mocks extensivamente

### Testes de Integração

Os testes de integração verificam o funcionamento conjunto de múltiplos componentes e fluxos completos.

**Características:**
- Mais lentos que unitários
- Testam fluxos completos
- Verificam integração entre módulos
- Simulam cenários reais de uso

## Fixtures Disponíveis

### Fixtures Globais (em `conftest.py`)

- `reset_environment` - Reseta variáveis de ambiente
- `sample_service_message` - Mensagem de exemplo para registro
- `sample_search_message` - Mensagem de exemplo para busca
- `mock_gemini_success_response` - Factory para respostas de sucesso
- `mock_gemini_error_response` - Factory para respostas de erro

### Fixtures por Arquivo

Veja cada arquivo de teste para fixtures específicas.

## Marcadores (Markers)

Os testes podem ser marcados com:

- `@pytest.mark.unit` - Teste unitário
- `@pytest.mark.integration` - Teste de integração
- `@pytest.mark.slow` - Teste lento
- `@pytest.mark.requires_api_key` - Teste que precisa de API key real

Exemplo de uso:

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_example():
    pass
```

## Configuração do Pytest

A configuração está em `pytest.ini`:

- Caminho de testes: `tests/`
- Padrão de arquivos: `test_*.py`
- Cobertura: `src/api_client/`
- Modo asyncio: `auto`

## Boas Práticas

1. **Nomeação:** Use nomes descritivos para testes
   - ✅ `test_process_message_without_api_key`
   - ❌ `test1`

2. **Organização:** Um arquivo de teste por módulo
   - `test_gemini_api_client.py` → `gemini_api_client.py`

3. **Isolamento:** Cada teste deve ser independente

4. **Mocking:** Mock dependências externas (APIs, banco de dados)

5. **Assertions:** Use assertions claras e específicas

6. **Documentação:** Docstrings explicam o que o teste verifica

## Troubleshooting

### Erro: "No module named 'src'"

Verifique se você está executando pytest do diretório raiz do projeto.

### Testes assíncronos não funcionam

Certifique-se que `pytest-asyncio` está instalado e que o teste tem `@pytest.mark.asyncio`.

### Erro de importação de módulos

Execute:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Cobertura não está funcionando

Instale `pytest-cov`:
```bash
pip install pytest-cov
```

## Próximos Passos

- [ ] Adicionar testes para outros módulos (repositories, schemas, etc.)
- [ ] Implementar testes E2E com a API real (marcados com `requires_api_key`)
- [ ] Adicionar testes de performance
- [ ] Configurar CI/CD para rodar testes automaticamente
- [ ] Aumentar cobertura para > 90%

## Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Pytest-Mock](https://pytest-mock.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
