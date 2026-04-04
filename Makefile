.PHONY: setup dev build test clean

setup:
	python3.12 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e ./tribev2
	.venv/bin/pip install uv
	@echo ""
	@echo "Done. Run 'source .venv/bin/activate' to activate."

dev:
	.venv/bin/uvicorn main:app --reload

test:
	.venv/bin/pytest tests/ -v

build:
	docker build -t neuro .

clean:
	rm -rf .venv __pycache__ .pytest_cache cache
