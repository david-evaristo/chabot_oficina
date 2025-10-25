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
from src.api_client.gemini_api_client import process_user_message
from src.api_client.gemini_audio_client import transcribe_audio
from src.schemas.chat_schemas import (
    CreateServiceSchema,
    CreateServiceData,
    SearchParamsSchema,
    SearchParamsData
)


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
        mock_client = MagicMock()
        expected_data = CreateServiceSchema(
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

        mock_response = MagicMock()
        mock_response.parsed = expected_data
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch('src.api_client.gemini_api_client.gemini_client', mock_client):
            user_message = """
            Registrar revisão do Civic da Maria Santos, telefone 11987654321,
            carro prata ano 2021, revisão dos 10.000 km, valor 450 reais,
            incluir troca de filtros
            """

            result, error = await process_user_message(user_message)

            assert error is None
            assert result is not None
            assert result.intent == "record_service"
            assert result.data.client_name == "Maria Santos"
            assert result.data.car_model == "Civic"
            assert result.data.service_valor == 450.00

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerationConfig')
    @patch('src.api_client.gemini_api_client.gemini_client')
    async def test_complete_service_search_flow(self, mock_gemini_client, mock_gen_config, mock_env_with_api_key):
        """
        Testa fluxo completo de busca de serviço:
        1. Usuário envia mensagem de busca
        2. Gemini classifica como search_service
        3. Parâmetros de busca são extraídos
        """
        expected_data = SearchParamsSchema(
            intent="search_service",
            search_params=SearchParamsData(
                client_name="Pedro",
                car_brand="Ford",
                car_model="Focus"
            )
        )

        mock_response = MagicMock()
        mock_response.parsed = expected_data
        mock_gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        user_message = "Buscar serviços do Pedro com Ford Focus"

        result, error = await process_user_message(user_message)

        assert error is None
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
        mock_client = MagicMock()
        transcription_text = "Registrar troca de óleo do Gol do Carlos, valor 120 reais"

        mock_transcription_response = MagicMock()
        mock_transcription_response.text = transcription_text

        # Mock para processamento
        service_data = CreateServiceSchema(
            intent="record_service",
            data=CreateServiceData(
                client_name="Carlos",
                car_model="Gol",
                service_description="Troca de óleo",
                service_valor=120.00
            )
        )

        mock_processing_response = MagicMock()
        mock_processing_response.parsed = service_data

        # Configurar mock para retornar diferentes respostas
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=[mock_transcription_response, mock_processing_response]
        )

        # Criar mock de arquivo de áudio
        mock_audio = MagicMock(spec=UploadFile)
        mock_audio.filename = "service_record.webm"
        mock_audio.content_type = "audio/webm"
        mock_audio.read = AsyncMock(return_value=b"fake audio bytes")

        with patch('src.api_client.gemini_audio_client.gemini_client', mock_client):
            with patch('src.api_client.gemini_api_client.gemini_client', mock_client):
                # Passo 1: Transcrever áudio
                transcribed = await transcribe_audio(mock_audio)
                assert transcribed == transcription_text

                # Passo 2: Processar texto transcrito
                result, error = await process_user_message(transcribed)

                assert error is None
                assert result.intent == "record_service"
                assert result.data.client_name == "Carlos"
                assert result.data.service_valor == 120.00


class TestErrorHandlingIntegration:
    """Testes de integração focados em tratamento de erros."""

    @pytest.mark.asyncio
    async def test_api_key_validation_across_modules(self):
        """Verifica que ambos os módulos validam corretamente a ausência de API key."""
        with patch('src.api_client.gemini_api_client.gemini_client', None):
            with patch('src.api_client.gemini_audio_client.gemini_client', None):
                # Testar process_user_message
                result, error = await process_user_message("teste")
                assert error == "API Key do Gemini não configurada"

                # Testar transcribe_audio
                mock_audio = MagicMock(spec=UploadFile)
                mock_audio.read = AsyncMock(return_value=b"data")

                with pytest.raises(HTTPException) as exc_info:
                    await transcribe_audio(mock_audio)
                assert "API Key do Gemini não configurada" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_error_propagation_in_pipeline(self, mock_env_with_api_key):
        """Testa propagação de erros ao longo do pipeline."""
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("Network timeout")
        )

        with patch('src.api_client.gemini_audio_client.gemini_client', mock_client):
            mock_audio = MagicMock(spec=UploadFile)
            mock_audio.filename = "test.webm"
            mock_audio.content_type = "audio/webm"
            mock_audio.read = AsyncMock(return_value=b"audio data")

            with pytest.raises(HTTPException) as exc_info:
                await transcribe_audio(mock_audio)

            assert "Erro na transcrição do áudio" in str(exc_info.value.detail)
            assert "Network timeout" in str(exc_info.value.detail)


class TestSchemaValidation:
    """Testes de integração com validação de schemas."""

    @pytest.mark.asyncio
    async def test_schema_validation_for_complete_service_data(self, mock_env_with_api_key):
        """Testa validação de schema com todos os campos preenchidos."""
        mock_client = MagicMock()

        complete_data = CreateServiceSchema(
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
        minimal_data = CreateServiceSchema(
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
        search_data = SearchParamsSchema(
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
    @patch('src.api_client.gemini_api_client.types.GenerationConfig')
    async def test_model_configuration_is_used(self, mock_gen_config, mock_env_with_api_key, monkeypatch):
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

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.parsed = MagicMock()

        mock_generate = AsyncMock(return_value=mock_response)
        mock_client.aio.models.generate_content = mock_generate

        with patch('src.api_client.gemini_api_client.gemini_client', mock_client):
            await gemini_api_client.process_user_message("teste")

            # Verificar que o modelo correto foi usado
            mock_generate.assert_called_once()
            call_args, call_kwargs = mock_generate.call_args
            assert call_kwargs.get("model") == custom_model


class TestConcurrentRequests:
    """Testes de integração para requisições concorrentes."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_transcriptions(self, mock_env_with_api_key):
        """Testa múltiplas transcrições simultâneas."""
        import asyncio

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Transcrição de áudio"

        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        # Criar múltiplos arquivos de áudio mock
        audio_files = []
        for i in range(5):
            mock_audio = MagicMock(spec=UploadFile)
            mock_audio.filename = f"audio_{i}.webm"
            mock_audio.content_type = "audio/webm"
            mock_audio.read = AsyncMock(return_value=f"audio data {i}".encode())
            audio_files.append(mock_audio)

        with patch('src.api_client.gemini_audio_client.gemini_client', mock_client):
            # Executar transcrições em paralelo
            tasks = [transcribe_audio(audio) for audio in audio_files]
            results = await asyncio.gather(*tasks)

            # Verificar que todas as transcrições foram bem-sucedidas
            assert len(results) == 5
            assert all(result == "Transcrição de áudio" for result in results)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_api_client.types.GenerationConfig')
    async def test_multiple_concurrent_message_processing(self, mock_gen_config, mock_env_with_api_key):
        """Testa múltiplos processamentos de mensagem simultâneos."""
        import asyncio

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.parsed = SearchParamsSchema(
            intent="search_service",
            search_params=SearchParamsData(client_name="Test")
        )

        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

        with patch('src.api_client.gemini_api_client.gemini_client', mock_client):
            messages = [f"Buscar serviço {i}" for i in range(5)]

            # Processar mensagens em paralelo
            tasks = [process_user_message(msg) for msg in messages]
            results = await asyncio.gather(*tasks)

            # Verificar que todos os processamentos foram bem-sucedidos
            assert len(results) == 5
            assert all(error is None for _, error in results)
            assert all(result.intent == "search_service" for result, _ in results)
