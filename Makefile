.PHONY: build serve clean install

install:
	npm install

build: clean
	mkdir -p build
	cp -ra static build/
	npm run build:css
	python build.py

serve: build
	uv run uvicorn server:app --reload --port 8000

clean:
	rm -rf build
