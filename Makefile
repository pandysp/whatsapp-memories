# Virtual Environment
# TODO: Automatic virtual environment creation?
.clean-venv:
	rm -rf .venv

.venv:
	uv sync

init: .clean-venv .venv

# Tests
test-%: .venv
	uv run pytest tests/$*

# Clear cached files
clear-cache:
	@echo "Clearing cache file (backend_cache.db)..."
	@echo "Note: If SQLITE_DB_PATH env var is set to a different location, you may need to delete that file manually."
	rm -f backend_cache.db
	@echo "Cache cleared."

# Linting
format:
	uv run ruff format backend

lint:
	uv run ruff check backend --fix

# Scripts & Services
start: .venv
	uv run python -m backend.process_whatsapp_messages $(ARGS)

run-backend: .venv
	uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

docker-run:
	docker run -p 8000:8000 marker

deploy:
	cdk deploy

# Frontend commands
run-frontend:
	cd frontend && pnpm dev

build-frontend:
	cd frontend && pnpm build

start-frontend:
	cd frontend && pnpm start

lint-frontend:
	cd frontend && pnpm lint

# Run both frontend and backend
dev-all:
	@echo "Starting backend and frontend concurrently..."
	pnpm dev:all

# Install dependencies
install:
	@echo "Installing pnpm workspace dependencies..."
	pnpm install
	@echo "Installing backend dependencies..."
	uv sync
	@echo "All dependencies installed."

# TODO: Cleanup
