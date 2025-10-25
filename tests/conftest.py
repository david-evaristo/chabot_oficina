"""
Configuração compartilhada para todos os testes.

Este arquivo contém fixtures e configurações que são compartilhadas
entre testes unitários e de integração.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Adicionar diretório raiz ao path para importações
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """
    Reseta o ambiente antes de cada teste para evitar efeitos colaterais.
    """
    # Configurar variáveis de ambiente padrão para testes
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest.fixture
def sample_service_message():
    """Fixture com mensagem de exemplo para registro de serviço."""
    return """
    Registrar serviço do João Silva, telefone 11999999999,
    Toyota Corolla preto ano 2020, troca de óleo,
    valor 150 reais, cliente pediu óleo sintético
    """


@pytest.fixture
def sample_search_message():
    """Fixture com mensagem de exemplo para busca de serviço."""
    return "Buscar serviços do João com Toyota"


@pytest.fixture
def mock_gemini_success_response():
    """
    Fixture que retorna um mock de resposta bem-sucedida do Gemini.
    Pode ser usado tanto para testes unitários quanto de integração.
    """
    def _create_response(parsed_data):
        mock_response = MagicMock()
        mock_response.parsed = parsed_data
        mock_response.text = "Mocked response text"
        return mock_response
    
    return _create_response


@pytest.fixture
def mock_gemini_error_response():
    """
    Fixture que simula um erro na resposta do Gemini.
    """
    def _create_error(error_message="API Error"):
        return Exception(error_message)
    
    return _create_error


# Configuração de logging para testes
@pytest.fixture(autouse=True)
def configure_test_logging(caplog):
    """
    Configura logging para testes.
    Captura logs mas não os exibe a menos que o teste falhe.
    """
    import logging
    caplog.set_level(logging.INFO)


# Fixture para limpar cache de módulos após testes
@pytest.fixture(autouse=True)
def cleanup_imports():
    """
    Limpa imports de módulos após cada teste para evitar
    que alterações em configuração afetem outros testes.
    """
    yield
    # Após o teste, podemos limpar módulos se necessário
    # (mantido simples por enquanto)


def pytest_configure(config):
    """
    Configuração executada antes de rodar os testes.
    """
    # Registrar marcadores customizados
    config.addinivalue_line(
        "markers", "unit: marca teste como unitário"
    )
    config.addinivalue_line(
        "markers", "integration: marca teste como de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca teste como lento"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marca teste que precisa de API key válida"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modifica items de teste durante a coleta.
    Adiciona marcadores automaticamente baseado no caminho do arquivo.
    """
    for item in items:
        # Adicionar marcador 'unit' para testes na pasta unit/
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Adicionar marcador 'integration' para testes na pasta integration/
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# Hook para relatório de testes
def pytest_report_header(config):
    """
    Adiciona informação extra ao cabeçalho do relatório de testes.
    """
    return [
        "Projeto: Mech AI - Sistema de Gerenciamento de Oficina Mecânica",
        "Módulo testado: src/api_client (Clientes da API Gemini)"
    ]
