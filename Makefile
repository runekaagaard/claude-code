.PHONY: build serve clean

build: clean
	mkdir -p build
	cp -ra static build
	python build.py

serve: clean build
	uv run uvicorn server:app --reload --port 8000

clean:
	rm -rf build
