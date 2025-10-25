# Makefile para facilitar execução de testes e tarefas comuns

.PHONY: help test test-unit test-integration test-cov test-fast clean install lint format

# Variáveis
PYTHON := python3
PYTEST := pytest
PIP := pip

# Ajuda
help:
	@echo "Comandos disponíveis:"
	@echo "  make install          - Instala dependências do projeto"
	@echo "  make test             - Executa todos os testes"
	@echo "  make test-unit        - Executa apenas testes unitários"
	@echo "  make test-integration - Executa apenas testes de integração"
	@echo "  make test-cov         - Executa testes com relatório de cobertura"
	@echo "  make test-fast        - Executa testes em paralelo (mais rápido)"
	@echo "  make test-watch       - Executa testes continuamente (modo watch)"
	@echo "  make clean            - Remove arquivos temporários e cache"
	@echo "  make lint             - Verifica qualidade do código"
	@echo "  make format           - Formata o código"

# Instalar dependências
install:
	@echo "Instalando dependências..."
	$(PIP) install -r requirements.txt

# Executar todos os testes
test:
	@echo "Executando todos os testes..."
	$(PYTEST) -v

# Executar apenas testes unitários
test-unit:
	@echo "Executando testes unitários..."
	$(PYTEST) -v -m unit tests/unit/

# Executar apenas testes de integração
test-integration:
	@echo "Executando testes de integração..."
	$(PYTEST) -v -m integration tests/integration/

# Executar testes com cobertura
test-cov:
	@echo "Executando testes com relatório de cobertura..."
	$(PYTEST) --cov=src/api_client --cov-report=html --cov-report=term-missing
	@echo "Relatório HTML gerado em htmlcov/index.html"

# Executar testes em paralelo
test-fast:
	@echo "Executando testes em paralelo..."
	@if ! $(PIP) show pytest-xdist > /dev/null 2>&1; then \
		echo "Instalando pytest-xdist..."; \
		$(PIP) install pytest-xdist; \
	fi
	$(PYTEST) -n auto

# Executar testes em modo watch
test-watch:
	@echo "Executando testes em modo watch..."
	@if ! $(PIP) show pytest-watch > /dev/null 2>&1; then \
		echo "Instalando pytest-watch..."; \
		$(PIP) install pytest-watch; \
	fi
	ptw -- -v

# Limpar arquivos temporários
clean:
	@echo "Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	@echo "Limpeza concluída!"

# Verificar qualidade do código
lint:
	@echo "Verificando qualidade do código..."
	@if ! $(PIP) show flake8 > /dev/null 2>&1; then \
		echo "Instalando flake8..."; \
		$(PIP) install flake8; \
	fi
	flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__,.git,migrations

# Formatar código
format:
	@echo "Formatando código..."
	@if ! $(PIP) show black > /dev/null 2>&1; then \
		echo "Instalando black..."; \
		$(PIP) install black; \
	fi
	black src/ tests/ --line-length=100

# Verificar tipos (opcional)
type-check:
	@echo "Verificando tipos..."
	@if ! $(PIP) show mypy > /dev/null 2>&1; then \
		echo "Instalando mypy..."; \
		$(PIP) install mypy; \
	fi
	mypy src/api_client/

# Executar teste específico
# Uso: make test-file FILE=tests/unit/test_gemini_api_client.py
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Uso: make test-file FILE=caminho/para/arquivo_test.py"; \
		exit 1; \
	fi
	$(PYTEST) -v $(FILE)

# Mostrar cobertura resumida
coverage-report:
	@if [ ! -f .coverage ]; then \
		echo "Execute 'make test-cov' primeiro para gerar relatório de cobertura"; \
		exit 1; \
	fi
	coverage report

# Abrir relatório HTML de cobertura
coverage-html:
	@if [ ! -d htmlcov ]; then \
		echo "Execute 'make test-cov' primeiro para gerar relatório HTML"; \
		exit 1; \
	fi
	@echo "Abrindo relatório HTML..."
	xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || echo "Abra manualmente: htmlcov/index.html"

# Verificar se há testes quebrados
test-quick:
	@echo "Executando verificação rápida..."
	$(PYTEST) -x --tb=short

# Executar testes com output detalhado
test-verbose:
	@echo "Executando testes com output detalhado..."
	$(PYTEST) -vv -s

# Instalar dependências de desenvolvimento
install-dev:
	@echo "Instalando dependências de desenvolvimento..."
	$(PIP) install -r requirements.txt
	$(PIP) install pytest-xdist pytest-watch black flake8 mypy

# Executar todos os checks antes de commit
pre-commit: clean format lint test
	@echo "✅ Todos os checks passaram! Pronto para commit."
