.PHONY: setup data check eval test dev dev-backend dev-frontend build-frontend clean

setup:
	pip install -r requirements.txt
	cd frontend && npm install

data:
	cd data && python generate_data.py --out raw
	python src/load.py --raw data/raw --db finance.duckdb --views src/semantic/views.sql

test:
	PYTHONPATH=. ./.venv/bin/pytest backend/tests/test_api.py -v

dev:
	./run_platform.sh

dev-backend:
	PYTHONPATH=. ./.venv/bin/uvicorn backend.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

build-frontend:
	cd frontend && npm run build

check:
	cd data && python generate_data.py --out /tmp/_smoke >/dev/null && echo "generator OK"

eval:
	python eval/score.py --answers eval/answer_key.yaml --input $(FILE)

clean:
	rm -f data/raw/*.csv

