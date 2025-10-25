
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import the function to be tested
from src.api_client.gemini_api_client import process_user_message
# Import schemas for creating test data
from src.schemas.chat_schemas import GeminiResponse, CreateServiceSchema, CreateServiceData


@pytest.mark.asyncio
async def test_process_user_message_no_api_key():
    """
    Test that an error is returned if the Gemini API key is not configured.
    """
    # Patch the module-level client to be None, simulating no API key.
    with patch('src.api_client.gemini_api_client.gemini_client', None):
        response, error = await process_user_message("some message")

    assert response is None
    assert "API Key do Gemini não configurada" in error


@pytest.mark.asyncio
@patch('src.api_client.gemini_api_client.types.GenerationConfig')
@patch('src.api_client.gemini_api_client.gemini_client')
async def test_process_user_message_success(mock_gemini_client, mock_generation_config):
    """
    Test the successful processing of a user message.
    """
    # 1. Arrange: Set up the mock client and expected response
    mock_response_data = GeminiResponse(
        intent="record_service",
        create_service_data=CreateServiceSchema(
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
    )

    # The Gemini client returns a response object with a 'parsed' attribute
    # containing the structured data.
    mock_api_response = MagicMock()
    mock_api_response.parsed = mock_response_data

    # Configure the mock's async method to return our mock response
    mock_gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_api_response)

    # 2. Act: Call the function
    response, error = await process_user_message("Registrar troca de óleo no Ford Ka")

    # 3. Assert: Check the results
    assert error is None
    assert response == mock_response_data
    mock_gemini_client.aio.models.generate_content.assert_called_once()
    mock_generation_config.assert_called_once()


@pytest.mark.asyncio
@patch('src.api_client.gemini_api_client.types.GenerationConfig')
@patch('src.api_client.gemini_api_client.gemini_client')
async def test_process_user_message_gemini_api_failure(mock_gemini_client, mock_generation_config):
    """
    Test the handling of a Gemini API failure.
    """
    # 1. Arrange: Configure the mock to raise an exception
    mock_gemini_client.aio.models.generate_content = AsyncMock(side_effect=Exception("Gemini API error"))

    # 2. Act: Call the function
    response, error = await process_user_message("Registrar troca de óleo no Ford Ka")

    # 3. Assert: Check that the error was caught and returned
    assert response is None
    assert "Gemini API error" in error
    mock_gemini_client.aio.models.generate_content.assert_called_once()
    mock_generation_config.assert_called_once()
