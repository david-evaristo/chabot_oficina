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