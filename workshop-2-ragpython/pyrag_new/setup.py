from setuptools import setup, find_packages

setup(
    name="ragdocs",
    version="0.1.0",
    description="A FastMCP server for RAG with documentation",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "mcp>=1.2.0",
        "qdrant-client>=1.7.0",
        "openai>=1.12.0",
        "pymupdf>=1.23.0",
        "beautifulsoup4>=4.12.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ragdocs=ragdocs.server:main",
        ],
    },
)
