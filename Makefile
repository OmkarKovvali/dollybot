.PHONY: check test-camera test-simulator

check: test-camera test-simulator

test-camera:
	uv run --frozen python -m unittest discover -s tests -v

test-simulator:
	node --test flowbase-sim/tests/*.test.mjs
