.PHONY: test

# Build the test image and run the unit suite. Fails if coverage is under 100%.
test:
	docker compose run --rm --build test
