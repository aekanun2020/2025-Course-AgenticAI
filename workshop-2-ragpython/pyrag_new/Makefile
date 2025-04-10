# Makefile for PyRAGDoc

.PHONY: install run-mcp run-fastmcp run-http

# Install the package
install:
	pip install -e .

# Run original MCP server
run-mcp:
	python run.py --mode mcp $(ARGS)

# Run FastMCP server
run-fastmcp:
	chmod +x run_fastmcp.sh
	./run_fastmcp.sh $(ARGS)

# Run HTTP server
run-http:
	python run.py --mode http $(ARGS)
