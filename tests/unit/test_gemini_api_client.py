from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

# Import the class to be tested
from src.api_client.gemini_api_client import GeminiAPIClient
from src.core.config import Config
# Import schemas for creating test data
from src.schemas.chat_schemas import GeminiResponse, CreateServiceData


@pytest.fixture
def mock_env_with_api_key(monkeypatch):
    """Configura ambiente com API key válida."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key-for-testing")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")


@pytest.mark.asyncio
async def test_gemini_api_client_no_api_key():
    """
    Test that a ValueError is raised if the Gemini API key is not configured.
    """
    with pytest.raises(ValueError) as exc_info:
        GeminiAPIClient(api_key="")
    assert "GEMINI_API_KEY não configurada." in str(exc_info.value)


@pytest.mark.asyncio
@patch('src.api_client.gemini_api_client.types.GenerateContentConfig')
@patch('src.api_client.gemini_api_client.genai.Client')
async def test_process_user_message_success(mock_genai_client, mock_generation_config, mock_env_with_api_key):
    """
    Test the successful processing of a user message.
    """
    # 1. Arrange: Set up the mock client and expected response
    mock_response_data = GeminiResponse(
        intent="record_service",
        data=CreateServiceData(
            car_brand="Ford",
            car_model="Ka",
            service_description="Troca de óleo",
            service_date="2023-10-26",
            service_valor=150.00,
            service_observations="Filtro de óleo também trocado",
            car_year=1995,
            car_color="Preto",
            client_name="Felipe",
            client_phone="16988888888"
        )
    )

    # The Gemini client returns a response object with a 'parsed' attribute
    # containing the structured data.
    mock_api_response = MagicMock()
    mock_api_response.parsed = mock_response_data

    # Configure the mock's async method to return our mock response
    mock_gemini_client_instance = MagicMock()
    mock_gemini_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_api_response)
    mock_genai_client.return_value = mock_gemini_client_instance

    gemini_api_client = GeminiAPIClient(api_key=Config.GEMINI_API_KEY)

    # 2. Act: Call the function
    response = await gemini_api_client.process_user_message("Registrar troca de óleo no Ford Ka")

    # 3. Assert: Check the results
    assert response == mock_response_data
    mock_gemini_client_instance.aio.models.generate_content.assert_called_once()
    mock_generation_config.assert_called_once()


@pytest.mark.asyncio
@patch('src.api_client.gemini_api_client.types.GenerateContentConfig')
@patch('src.api_client.gemini_api_client.genai.Client')
async def test_process_user_message_gemini_api_failure(mock_genai_client, mock_generation_config, mock_env_with_api_key):
    """
    Test the handling of a Gemini API failure.
    """
    # 1. Arrange: Configure the mock to raise an exception
    mock_gemini_client_instance = MagicMock()
    mock_gemini_client_instance.aio.models.generate_content = AsyncMock(side_effect=Exception("Gemini API error"))
    mock_genai_client.return_value = mock_gemini_client_instance

    gemini_api_client = GeminiAPIClient(api_key=Config.GEMINI_API_KEY)

    # 2. Act: Call the function and assert HTTPException is raised
    with pytest.raises(HTTPException) as exc_info:
        await gemini_api_client.process_user_message("Registrar troca de óleo no Ford Ka")

    # 3. Assert: Check that the error was caught and returned
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Ocorreu um erro inesperado: Gemini API error" in exc_info.value.detail
    mock_gemini_client_instance.aio.models.generate_content.assert_called_once()
    mock_generation_config.assert_called_once()
