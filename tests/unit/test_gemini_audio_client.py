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
from src.api_client.gemini_audio_client import transcribe_audio


@pytest.fixture
def mock_gemini_client():
    """Fixture que cria um mock do cliente Gemini."""
    mock_client = MagicMock()
    mock_client.aio = MagicMock()
    mock_client.aio.models = MagicMock()
    return mock_client


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


class TestTranscribeAudio:
    """Testes para a função transcribe_audio."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_without_api_key(self, mock_audio_file):
        """Testa comportamento quando API key não está configurada."""
        with patch('src.api_client.gemini_audio_client.gemini_client', None):
            with pytest.raises(HTTPException) as exc_info:
                await transcribe_audio(mock_audio_file)
            
            assert exc_info.value.status_code == 500
            assert "API Key do Gemini não configurada" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(
        self, mock_gemini_client, mock_audio_file, mock_transcription_response
    ):
        """Testa transcrição bem-sucedida de arquivo de áudio."""
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            return_value=mock_transcription_response
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            result = await transcribe_audio(mock_audio_file)
            
            assert result == "Troca de óleo do Corolla do cliente João Silva"
            assert mock_audio_file.read.called
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_empty_file(
        self, mock_gemini_client, mock_empty_audio_file
    ):
        """Testa erro ao tentar transcrever arquivo vazio."""
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            with pytest.raises(HTTPException) as exc_info:
                await transcribe_audio(mock_empty_audio_file)
            
            assert exc_info.value.status_code == 400
            assert "Arquivo de áudio vazio" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_api_error(
        self, mock_gemini_client, mock_audio_file
    ):
        """Testa tratamento de erro durante chamada à API."""
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            side_effect=Exception("API Error: Invalid audio format")
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            with pytest.raises(HTTPException) as exc_info:
                await transcribe_audio(mock_audio_file)
            
            assert exc_info.value.status_code == 500
            assert "Erro na transcrição do áudio" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_empty_transcription(
        self, mock_gemini_client, mock_audio_file
    ):
        """Testa erro quando transcrição retorna texto vazio."""
        mock_response = MagicMock()
        mock_response.text = "   "  # String vazia após strip
        
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            with pytest.raises(HTTPException) as exc_info:
                await transcribe_audio(mock_audio_file)
            
            assert exc_info.value.status_code == 400
            assert "Transcrição retornou texto vazio" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_verifies_content_parts(
        self, mock_gemini_client, mock_audio_file, mock_transcription_response
    ):
        """Testa se os parâmetros corretos são enviados para a API."""
        mock_generate = AsyncMock(return_value=mock_transcription_response)
        mock_gemini_client.aio.models.generate_content = mock_generate
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            await transcribe_audio(mock_audio_file)
            
            # Verificar que a função foi chamada
            assert mock_generate.called
            
            # Verificar argumentos da chamada
            call_args = mock_generate.call_args
            assert 'model' in call_args.kwargs
            assert 'contents' in call_args.kwargs
            assert 'config' in call_args.kwargs
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_different_mime_types(
        self, mock_gemini_client, mock_transcription_response
    ):
        """Testa transcrição com diferentes tipos MIME."""
        mime_types = ['audio/webm', 'audio/mp3', 'audio/wav', 'audio/ogg']
        
        for mime_type in mime_types:
            mock_file = MagicMock(spec=UploadFile)
            mock_file.filename = f"test.{mime_type.split('/')[1]}"
            mock_file.content_type = mime_type
            mock_file.read = AsyncMock(return_value=b"audio data")
            
            mock_gemini_client.aio.models.generate_content = AsyncMock(
                return_value=mock_transcription_response
            )
            
            with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
                result = await transcribe_audio(mock_file)
                assert result == mock_transcription_response.text
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_without_content_type(
        self, mock_gemini_client, mock_transcription_response
    ):
        """Testa transcrição quando content_type é None (usa fallback)."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.webm"
        mock_file.content_type = None  # Sem content type
        mock_file.read = AsyncMock(return_value=b"audio data")
        
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            return_value=mock_transcription_response
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            result = await transcribe_audio(mock_file)
            
            # Deve usar o fallback 'audio/webm'
            assert result == mock_transcription_response.text
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_large_file(
        self, mock_gemini_client, mock_transcription_response
    ):
        """Testa transcrição de arquivo grande."""
        # Simular arquivo de 5MB
        large_audio_data = b"x" * (5 * 1024 * 1024)
        
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "large_audio.webm"
        mock_file.content_type = "audio/webm"
        mock_file.read = AsyncMock(return_value=large_audio_data)
        
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            return_value=mock_transcription_response
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            result = await transcribe_audio(mock_file)
            assert result == mock_transcription_response.text
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_config_parameters(
        self, mock_gemini_client, mock_audio_file, mock_transcription_response
    ):
        """Testa se os parâmetros de configuração estão corretos."""
        mock_generate = AsyncMock(return_value=mock_transcription_response)
        mock_gemini_client.aio.models.generate_content = mock_generate
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            await transcribe_audio(mock_audio_file)
            
            call_args = mock_generate.call_args
            
            # Verificar modelo
            assert call_args.kwargs['model'] == 'gemini-2.5-flash'
            
            # Verificar configuração
            config = call_args.kwargs['config']
            assert config.temperature == 0.1
            assert config.max_output_tokens == 1000
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_strips_whitespace(
        self, mock_gemini_client, mock_audio_file
    ):
        """Testa se o texto retornado tem espaços em branco removidos."""
        mock_response = MagicMock()
        mock_response.text = "   Transcrição com espaços   \n\n"
        
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            result = await transcribe_audio(mock_audio_file)
            assert result == "Transcrição com espaços"
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_special_characters(
        self, mock_gemini_client, mock_audio_file
    ):
        """Testa transcrição com caracteres especiais."""
        mock_response = MagicMock()
        mock_response.text = "Troca de óleo & filtro (R$ 150,00) - João's car"
        
        mock_gemini_client.aio.models.generate_content = AsyncMock(
            return_value=mock_response
        )
        
        with patch('src.api_client.gemini_audio_client.gemini_client', mock_gemini_client):
            result = await transcribe_audio(mock_audio_file)
            assert result == mock_response.text
