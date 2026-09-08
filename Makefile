.PHONY: api web test

api:
	uvicorn jarvis_api.main:app --app-dir services/api --reload --port 8000

web:
	npm --prefix apps/web run dev

test:
	pytest
	npm --prefix apps/web run build
