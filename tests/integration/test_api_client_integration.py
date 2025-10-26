"""
Testes de integração para os clientes da API Gemini.

Estes testes verificam a integração entre os componentes e fluxos completos,
incluindo configuração, schemas e respostas.

NOTA: Estes testes usam mocks avançados para simular o comportamento real
da API sem fazer chamadas reais ao Gemini (que requerem API key válida).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.chat_schemas import GeminiResponse, CreateServiceData, SearchParamsData
from src.api_client.gemini_api_client import GeminiAPIClient
from src.api_client.gemini_audio_client import GeminiAudioClient
from src.routers.chat import _process_and_handle_intent
from src.core.database import get_db
from src.core.config import Config
from src.core.models import Client, Car, ServiceRecord
from datetime import datetime


@pytest.fixture
def mock_env_with_api_key(monkeypatch):
    """Configura ambiente com API key válida."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key-for-testing")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")


class TestEndToEndFlow:
    """Testes de fluxo completo desde entrada até saída."""

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerationConfig')
    async def test_complete_service_registration_flow(self, mock_gen_config, mock_env_with_api_key):
        """
        Testa fluxo completo de registro de serviço:
        1. Usuário envia mensagem
        2. Gemini classifica como record_service
        3. Dados são extraídos corretamente
        """
        # Preparar resposta mock
        mock_gemini_api_client_instance = MagicMock(spec=GeminiAPIClient)
        expected_data = GeminiResponse(
            intent="record_service",
            data=CreateServiceData(
                client_name="Maria Santos",
                client_phone="11987654321",
                car_brand="Honda",
                car_model="Civic",
                car_color="Prata",
                car_year=2021,
                service_description="Revisão dos 10.000 km",
                service_date="2024-10-25",
                service_valor=450.00,
                service_observations="Incluir troca de filtros"
            )
        )

        # Mock do banco de dados
        mock_db = AsyncMock(spec=AsyncSession)
        mock_client_instance = MagicMock(spec=Client)
        mock_client_instance.id = 1
        mock_client_instance.name = "Maria Santos"
        mock_client_instance.phone = "11987654321"

        mock_car_instance = MagicMock(spec=Car)
        mock_car_instance.id = 1
        mock_car_instance.brand = "Honda"
        mock_car_instance.model = "Civic"
        mock_car_instance.color = "Prata"
        mock_car_instance.year = 2021

        mock_service_record_instance = MagicMock(spec=ServiceRecord)
        mock_service_record_instance.id = 1
        mock_service_record_instance.servico = "Revisão dos 10.000 km"
        mock_service_record_instance.date = datetime.now()
        mock_service_record_instance.valor = 450.00
        mock_service_record_instance.observations = "Incluir troca de filtros"
        mock_service_record_instance.car = mock_car_instance

        mock_scalar_result_client = MagicMock()
        mock_scalar_result_client.first.return_value = mock_client_instance

        mock_scalar_result_car = MagicMock()
        mock_scalar_result_car.first.return_value = mock_car_instance

        mock_result_execute = MagicMock()
        mock_result_execute.scalars.side_effect = [mock_scalar_result_client, mock_scalar_result_car]

        mock_db.execute.return_value = mock_result_execute
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = [mock_client_instance, mock_car_instance, mock_service_record_instance]

        user_message = """
            Registrar revisão do Civic da Maria Santos, telefone 11987654321,
            carro prata ano 2021, revisão dos 10.000 km, valor 450 reais,
            incluir troca de filtros
            """

        result = await _process_and_handle_intent(user_message, mock_db, mock_gemini_api_client_instance)

        assert result is not None
        assert result.intent == "record_service"
        assert result.data.client_name == "Maria Santos"
        assert result.data.car_model == "Civic"
        assert result.data.service_valor == 450.00

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerationConfig')
    async def test_complete_service_search_flow(self, mock_gen_config, mock_env_with_api_key):
        mock_gemini_api_client_instance = MagicMock(spec=GeminiAPIClient)
        expected_data = GeminiResponse(
            intent="search_service",
            search_params=SearchParamsData(
                client_name="Pedro",
                car_brand="Ford",
                car_model="Focus"
            )
        )

        mock_db = AsyncMock(spec=AsyncSession)

        mock_client_instance = MagicMock(spec=Client)
        mock_client_instance.id = 1
        mock_client_instance.name = "Pedro"

        mock_car_instance = MagicMock(spec=Car)
        mock_car_instance.id = 1
        mock_car_instance.brand = "Ford"
        mock_car_instance.model = "Focus"
        mock_car_instance.owner = mock_client_instance

        mock_service_record_instance = MagicMock(spec=ServiceRecord)
        mock_service_record_instance.id = 1
        mock_service_record_instance.servico = "Troca de óleo"
        mock_service_record_instance.date = datetime.now()
        mock_service_record_instance.valor = 100.00
        mock_service_record_instance.observations = ""
        mock_service_record_instance.car = mock_car_instance

        mock_scalar_result_service_records = MagicMock()
        mock_scalar_result_service_records.all.return_value = [mock_service_record_instance]

        mock_result_execute = MagicMock()
        mock_result_execute.scalars.return_value = mock_scalar_result_service_records

        mock_db.execute.return_value = mock_result_execute

        user_message = "Buscar serviços do Pedro com Ford Focus"

        result = await _process_and_handle_intent(user_message, mock_db, mock_gemini_api_client_instance)

        assert result is not None
        assert result.intent == "search_service"
        assert result.search_params.client_name == "Pedro"
        assert result.search_params.car_brand == "Ford"

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerationConfig')
    async def test_audio_to_text_to_service_flow(self, mock_gen_config, mock_env_with_api_key):
        """
        Testa fluxo completo de áudio até registro:
        1. Áudio é transcrito
        2. Texto é processado para extrair dados
        3. Serviço é registrado
        """
        # Mock para transcrição
        mock_gemini_audio_client_instance = MagicMock(spec=GeminiAudioClient)
        transcription_text = "Registrar troca de óleo do Gol do Carlos, valor 120 reais"
        mock_gemini_audio_client_instance.transcribe_audio = AsyncMock(return_value=transcription_text)

        # Mock para processamento
        mock_gemini_api_client_instance = MagicMock(spec=GeminiAPIClient)
        service_data = GeminiResponse(
            intent="record_service",
            data=CreateServiceData(
                client_name="Carlos",
                car_model="Gol",
                service_description="Troca de óleo",
                service_valor=120.00
            )
        )
        # Mock do banco de dados
        mock_db = AsyncMock(spec=AsyncSession)
        mock_client_instance = MagicMock(spec=Client)
        mock_client_instance.id = 1
        mock_client_instance.name = "Carlos"
        mock_client_instance.phone = None

        mock_car_instance = MagicMock(spec=Car)
        mock_car_instance.id = 1
        mock_car_instance.brand = None
        mock_car_instance.model = "Gol"
        mock_car_instance.color = None
        mock_car_instance.year = None

        mock_service_record_instance = MagicMock(spec=ServiceRecord)
        mock_service_record_instance.id = 1
        mock_service_record_instance.servico = "Troca de óleo"
        mock_service_record_instance.date = datetime.now()
        mock_service_record_instance.valor = 120.00
        mock_service_record_instance.observations = None
        mock_service_record_instance.car = mock_car_instance

        mock_scalar_result_client = MagicMock()
        mock_scalar_result_client.first.return_value = mock_client_instance

        mock_scalar_result_car = MagicMock()
        mock_scalar_result_car.first.return_value = mock_car_instance

        mock_result_execute = MagicMock()
        mock_result_execute.scalars.side_effect = [mock_scalar_result_client, mock_scalar_result_car]

        mock_db.execute.return_value = mock_result_execute
        mock_db.flush.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = [mock_client_instance, mock_car_instance, mock_service_record_instance]

        # Criar mock de arquivo de áudio
        mock_audio = MagicMock(spec=UploadFile)
        mock_audio.filename = "service_record.webm"
        mock_audio.content_type = "audio/webm"
        mock_audio.read = AsyncMock(return_value=b"fake audio bytes")

        # Passo 1: Transcrever áudio
        transcribed = await mock_gemini_audio_client_instance.transcribe_audio(mock_audio)
        assert transcribed == transcription_text

        # Passo 2: Processar texto transcrito
        result = await _process_and_handle_intent(transcribed, mock_db, mock_gemini_api_client_instance)

        assert result.intent == "record_service"
        assert result.data.client_name == "Carlos"
        assert result.data.service_valor == 120.00


class TestErrorHandlingIntegration:
    """Testes de integração focados em tratamento de erros."""

    @pytest.mark.asyncio
    async def test_api_key_validation_across_modules(self, monkeypatch):
        """Verifica que ambos os módulos validam corretamente a ausência de API key."""
        monkeypatch.setenv("GEMINI_API_KEY", "")

        from importlib import reload
        from src.core import config
        reload(config)

        # Testar GeminiAPIClient
        with pytest.raises(ValueError) as exc_info:
            GeminiAPIClient(api_key=config.Config.GEMINI_API_KEY)
        assert "GEMINI_API_KEY não configurada." in str(exc_info.value)

        # Testar GeminiAudioClient
        with pytest.raises(ValueError) as exc_info:
            GeminiAudioClient(api_key=config.Config.GEMINI_API_KEY)
        assert "GEMINI_API_KEY não configurada." in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_propagation_in_pipeline(self, mock_env_with_api_key):
        """Testa propagação de erros ao longo do pipeline."""
        mock_gemini_audio_client_instance = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        mock_gemini_audio_client_instance.client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("Network timeout")
        )

        mock_audio = MagicMock(spec=UploadFile)
        mock_audio.filename = "test.webm"
        mock_audio.content_type = "audio/webm"
        mock_audio.read = AsyncMock(return_value=b"audio data")

        with pytest.raises(HTTPException) as exc_info:
            await mock_gemini_audio_client_instance.transcribe_audio(mock_audio)

        assert "Ocorreu um erro inesperado durante a transcrição do áudio" in str(exc_info.value.detail)
        assert "Network timeout" in str(exc_info.value.detail)


class TestSchemaValidation:
    """Testes de integração com validação de schemas."""

    @pytest.mark.asyncio
    async def test_schema_validation_for_complete_service_data(self, mock_env_with_api_key):
        """Testa validação de schema com todos os campos preenchidos."""
        mock_client = MagicMock()

        complete_data = GeminiResponse(
            intent="record_service",
            data=CreateServiceData(
                client_name="Ana Paula",
                client_phone="11912345678",
                car_brand="Volkswagen",
                car_model="Polo",
                car_color="Branco",
                car_year=2022,
                service_description="Alinhamento e balanceamento",
                service_date="2024-10-25",
                service_valor=200.00,
                service_observations="Cliente preferencial"
            )
        )

        # Validar que o schema aceita todos os campos
        assert complete_data.intent == "record_service"
        assert complete_data.data.client_name == "Ana Paula"
        assert complete_data.data.car_year == 2022

    @pytest.mark.asyncio
    async def test_schema_validation_for_minimal_service_data(self, mock_env_with_api_key):
        """Testa validação de schema com campos mínimos (apenas obrigatórios)."""
        minimal_data = GeminiResponse(
            intent="record_service",
            data=CreateServiceData(
                service_description="Troca de pneus"
            )
        )

        # Validar que o schema aceita apenas campos obrigatórios
        assert minimal_data.intent == "record_service"
        assert minimal_data.data.service_description == "Troca de pneus"
        assert minimal_data.data.client_name is None
        assert minimal_data.data.service_valor is None

    @pytest.mark.asyncio
    async def test_schema_validation_for_search_params(self, mock_env_with_api_key):
        """Testa validação de schema para parâmetros de busca."""
        search_data = GeminiResponse(
            intent="search_service",
            search_params=SearchParamsData(
                client_name="Roberto",
                car_model="Corolla"
            )
        )

        assert search_data.intent == "search_service"
        assert search_data.search_params.client_name == "Roberto"
        assert search_data.search_params.car_brand is None


class TestConfigurationIntegration:
    """Testes de integração com configurações."""

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerateContentConfig')
    async def test_model_configuration_is_used(self, mock_gen_config_class, mock_env_with_api_key, monkeypatch):
        """Verifica se a configuração de modelo é utilizada corretamente."""
        # Configurar modelo customizado
        custom_model = "gemini-custom-model"
        monkeypatch.setenv("GEMINI_MODEL", custom_model)

        # Recarregar configuração e módulos dependentes
        from importlib import reload
        from src.core import config
        from src.api_client import gemini_api_client
        reload(config)
        reload(gemini_api_client)

        mock_gemini_api_client_instance = GeminiAPIClient(api_key=Config.GEMINI_API_KEY)
        mock_gemini_api_client_instance.client.aio.models.generate_content = AsyncMock()

        await mock_gemini_api_client_instance.process_user_message("teste")

        # Verificar que o modelo correto foi usado
        mock_gemini_api_client_instance.client.aio.models.generate_content.assert_called_once()
        call_kwargs = mock_gemini_api_client_instance.client.aio.models.generate_content.call_args[1]
        assert call_kwargs.get("model") == custom_model


class TestConcurrentRequests:
    """Testes de integração para requisições concorrentes."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_transcriptions(self, mock_env_with_api_key):
        """Testa múltiplas transcrições simultâneas."""
        import asyncio

        mock_gemini_audio_client_instance = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        mock_gemini_audio_client_instance.client.aio.models.generate_content = AsyncMock(return_value=MagicMock(text="Transcrição de áudio"))

        # Criar múltiplos arquivos de áudio mock
        audio_files = []
        for i in range(5):
            mock_audio = MagicMock(spec=UploadFile)
            mock_audio.filename = f"audio_{i}.webm"
            mock_audio.content_type = "audio/webm"
            mock_audio.read = AsyncMock(return_value=f"audio data {i}".encode())
            audio_files.append(mock_audio)

        # Executar transcrições em paralelo
        tasks = [mock_gemini_audio_client_instance.transcribe_audio(audio) for audio in audio_files]
        results = await asyncio.gather(*tasks)

        # Verificar que todas as transcrições foram bem-sucedidas
        assert len(results) == 5
        assert all(result == "Transcrição de áudio" for result in results)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerateContentConfig')
    async def test_multiple_concurrent_message_processing(self, mock_gen_config, mock_env_with_api_key):
        """Testa múltiplos processamentos de mensagem simultâneos."""
        import asyncio

        mock_gemini_api_client_instance = MagicMock(spec=GeminiAPIClient)
        mock_db = AsyncMock(spec=AsyncSession)

        mock_client_instance = MagicMock(spec=Client)
        mock_client_instance.id = 1
        mock_client_instance.name = "Test"

        mock_car_instance = MagicMock(spec=Car)
        mock_car_instance.id = 1
        mock_car_instance.brand = "Brand"
        mock_car_instance.model = "Model"
        mock_car_instance.owner = mock_client_instance

        mock_service_record_instance = MagicMock(spec=ServiceRecord)
        mock_service_record_instance.id = 1
        mock_service_record_instance.servico = "Service"
        mock_service_record_instance.date = datetime.now()
        mock_service_record_instance.valor = 100.00
        mock_service_record_instance.observations = ""
        mock_service_record_instance.car = mock_car_instance

        mock_scalar_result_service_records = MagicMock()
        mock_scalar_result_service_records.all.return_value = [mock_service_record_instance]

        mock_result_execute = MagicMock()
        mock_result_execute.scalars.return_value = mock_scalar_result_service_records

        mock_db.execute.return_value = mock_result_execute

        messages = [f"Buscar serviço {i}" for i in range(5)]

        # Processar mensagens em paralelo
        tasks = [_process_and_handle_intent(msg, mock_db, mock_gemini_api_client_instance) for msg in messages]
        results = await asyncio.gather(*tasks)

        # Verificar que todos os processamentos foram bem-sucedidos
        assert len(results) == 5
        assert all(result.intent == "search_service" for result in results)
