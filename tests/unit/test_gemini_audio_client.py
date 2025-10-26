"""
Testes unitários para o módulo gemini_audio_client.

Testa a função transcribe_audio com diferentes cenários:
- Sucesso na transcrição
- Erro quando API Key não está configurada
- Erro com arquivo vazio
- Erro durante chamada à API
- Validação de tipos MIME
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from io import BytesIO
from src.api_client.gemini_audio_client import GeminiAudioClient
from src.core.config import Config


@pytest.fixture
def mock_audio_file():
    """Fixture que cria um mock de arquivo de áudio."""
    audio_data = b"fake audio data content"
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_audio.webm"
    mock_file.content_type = "audio/webm"
    mock_file.read = AsyncMock(return_value=audio_data)
    
    return mock_file


@pytest.fixture
def mock_empty_audio_file():
    """Fixture que cria um mock de arquivo de áudio vazio."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "empty_audio.webm"
    mock_file.content_type = "audio/webm"
    mock_file.read = AsyncMock(return_value=b"")
    
    return mock_file


@pytest.fixture
def mock_transcription_response():
    """Fixture que simula uma resposta de transcrição bem-sucedida."""
    mock_response = MagicMock()
    mock_response.text = "Troca de óleo do Corolla do cliente João Silva"
    return mock_response


@pytest.fixture
def mock_env_with_api_key(monkeypatch):
    """Configura ambiente com API key válida."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key-for-testing")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")


class TestGeminiAudioClient:
    """Testes para a classe GeminiAudioClient."""
    
    @pytest.mark.asyncio
    async def test_gemini_audio_client_no_api_key(self):
        """
        Testa que um ValueError é levantado quando a API key não está configurada.
        """
        with pytest.raises(ValueError) as exc_info:
            GeminiAudioClient(api_key="")
        assert "GEMINI_API_KEY não configurada." in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_success(
        self, mock_genai_client, mock_audio_file, mock_transcription_response, mock_env_with_api_key
    ):
        """Testa transcrição bem-sucedida de arquivo de áudio."""
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            return_value=mock_transcription_response
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        result = await client.transcribe_audio(mock_audio_file)
            
        assert result == "Troca de óleo do Corolla do cliente João Silva"
        assert mock_audio_file.read.called
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)
        mock_gemini_client_instance.aio.models.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_with_empty_file(
        self, mock_genai_client, mock_empty_audio_file, mock_env_with_api_key
    ):
        """Testa erro ao tentar transcrever arquivo vazio."""
        mock_gemini_client_instance = MagicMock()
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        with pytest.raises(HTTPException) as exc_info:
            await client.transcribe_audio(mock_empty_audio_file)
            
        assert exc_info.value.status_code == 400
        assert "Arquivo de áudio vazio" in exc_info.value.detail
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)
        mock_gemini_client_instance.aio.models.generate_content.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_with_api_error(
        self, mock_genai_client, mock_audio_file, mock_env_with_api_key
    ):
        """
        Testa tratamento de erro durante chamada à API.
        """
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API Error: Invalid audio format")
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        with pytest.raises(HTTPException) as exc_info:
            await client.transcribe_audio(mock_audio_file)
            
        assert exc_info.value.status_code == 500
        assert ('Ocorreu um erro inesperado durante a transcrição do áudio: API Error: Invalid audio format') in exc_info.value.detail
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)
        mock_gemini_client_instance.aio.models.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_with_empty_transcription(
        self, mock_genai_client, mock_audio_file, mock_env_with_api_key
    ):
        """
        Testa erro quando transcrição retorna texto vazio.
        """
        mock_response = MagicMock()
        mock_response.text = "   "  # String vazia após strip
        
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        with pytest.raises(HTTPException) as exc_info:
            await client.transcribe_audio(mock_audio_file)
            
        assert exc_info.value.status_code == 400
        assert "Transcrição retornou texto vazio" in exc_info.value.detail
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)
        mock_gemini_client_instance.aio.models.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_verifies_content_parts(
        self, mock_genai_client, mock_audio_file, mock_transcription_response, mock_env_with_api_key
    ):
        """Testa se os parâmetros corretos são enviados para a API."""
        mock_gemini_client_instance = MagicMock()
        mock_generate = AsyncMock(return_value=mock_transcription_response)
        mock_gemini_client_instance.aio.models.generate_content = mock_generate
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        await client.transcribe_audio(mock_audio_file)
            
        # Verificar que a função foi chamada
        assert mock_generate.called
            
        # Verificar argumentos da chamada
        call_args = mock_generate.call_args
        assert 'model' in call_args.kwargs
        assert 'contents' in call_args.kwargs
        assert 'config' in call_args.kwargs
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_with_different_mime_types(
        self, mock_genai_client, mock_transcription_response, mock_env_with_api_key
    ):
        """Testa transcrição com diferentes tipos MIME."""
        mime_types = ['audio/webm', 'audio/mp3', 'audio/wav', 'audio/ogg']
        
        for mime_type in mime_types:
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = f"test.{mime_type.split('/')[1]}"
            mock_file.content_type = mime_type
            mock_file.read = AsyncMock(return_value=b"audio data")
            
            mock_gemini_client_instance = MagicMock()
            mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
                return_value=mock_transcription_response
            )
            mock_genai_client.return_value = mock_gemini_client_instance

            client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
            result = await client.transcribe_audio(mock_file)
            assert result == mock_transcription_response.text
            mock_genai_client.assert_called_with(api_key=Config.GEMINI_API_KEY)
            mock_genai_client.reset_mock()
    
    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_without_content_type(
        self, mock_genai_client, mock_transcription_response, mock_env_with_api_key
    ):
        """Testa transcrição quando content_type é None (usa fallback)."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.webm"
        mock_file.content_type = None  # Sem content type
        mock_file.read = AsyncMock(return_value=b"audio data")
        
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            return_value=mock_transcription_response
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        result = await client.transcribe_audio(mock_file)
            
        # Deve usar o fallback 'audio/webm'
        assert result == mock_transcription_response.text
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_with_large_file(
        self, mock_genai_client, mock_transcription_response, mock_env_with_api_key
    ):
        """
        Testa transcrição de arquivo grande.
        """
        # Simular arquivo de 5MB
        large_audio_data = b"x" * (5 * 1024 * 1024)
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "large_audio.webm"
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=large_audio_data)
        
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            return_value=mock_transcription_response
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        result = await client.transcribe_audio(mock_file)
        assert result == mock_transcription_response.text
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_config_parameters(
        self, mock_genai_client, mock_audio_file, mock_transcription_response, mock_env_with_api_key
    ):
        """
        Testa se os parâmetros de configuração estão corretos.
        """
        mock_gemini_client_instance = MagicMock()
        mock_generate = AsyncMock(return_value=mock_transcription_response)
        mock_gemini_client_instance.aio.models.generate_content = mock_generate
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        await client.transcribe_audio(mock_audio_file)
            
        call_args = mock_generate.call_args
            
        # Verificar modelo
        assert call_args.kwargs['model'] == Config.GEMINI_MODEL
            
        # Verificar configuração
        config = call_args.kwargs['config']
        assert config.temperature == 0.1
        assert config.max_output_tokens == 1000
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_strips_whitespace(
        self, mock_genai_client, mock_audio_file, mock_env_with_api_key
    ):
        """
        Testa se o texto retornado tem espaços em branco removidos.
        """
        mock_response = MagicMock()
        mock_response.text = "   Transcrição com espaços   \n\n"
        
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        result = await client.transcribe_audio(mock_audio_file)
        assert result == "Transcrição com espaços"
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)

    @pytest.mark.asyncio
    @patch('src.api_client.gemini_audio_client.genai.Client')
    async def test_transcribe_audio_with_special_characters(
        self, mock_genai_client, mock_audio_file, mock_env_with_api_key
    ):
        """
        Testa transcrição com caracteres especiais.
        """
        mock_response = MagicMock()
        mock_response.text = "Troca de óleo & filtro (R$ 150,00) - João's car"
        
        mock_gemini_client_instance = MagicMock()
        mock_gemini_client_instance.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        mock_genai_client.return_value = mock_gemini_client_instance

        client = GeminiAudioClient(api_key=Config.GEMINI_API_KEY)
        result = await client.transcribe_audio(mock_audio_file)
        assert result == mock_response.text
        mock_genai_client.assert_called_once_with(api_key=Config.GEMINI_API_KEY)
