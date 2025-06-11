# to.ci Portal Backend
The backend services for the to.ci Portal.

[![Code style: black][black-image]][black-url]
[![Imports: reorder-python-imports][imports-image]][imports-url]
[![Pydantic v2][pydantic-image]][pydantic-url]
[![pre-commit][pre-commit-image]][pre-commit-url]
[![License MIT][license-image]][license-url]

The backend provides the LLM services for the to.ci Portal. The backend integrates with the registry to find MCP servers.

## Features

* RESTful API endpoints
* Integration with registry
* API documentation with OpenAPI/Swagger

## Installation

```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

docker compose -f docker-compose.yml -f docker-compose-debug.yml up -d
```

## Project Structure

```
portal_backend/
├── alembic/              # Database migrations
├── cicd/                 # Scripts for CI/CD (deployment)
├── logs/                 # Reserved for logs
├── scripts/              # Scripts for running the server
├── src/                  # Core functionality
│   ├── agents/           # Agents service
│   ├── chats/            # Chats service
│   ├── darp_servers/     # DARP management service
│   └── database/         # Database schemas
│   └── llm_clients/      # LLM clients service
│   └── messages/         # Messages service
│   └── prompts/          # Prompts service
│   └── users/            # Users service
│   └── main.py           # Main entry point
│   └── settings.py       # Settings
```

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Prerequisites

* Python 3.10+
* Docker

### Local Development Setup

1. Start the development server:
```bash
uvicorn src.main:app --reload
```

### Code Style

We use:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run the pre-commit hooks to ensure code quality:

```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

Please read [CONTRIBUTING.md](../CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

The to.ci Portal Backend codebase is under MIT license.

<br>

[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black
[imports-image]: https://img.shields.io/badge/%20imports-reorder_python_imports-%231674b1?style=flat&labelColor=ef8336
[imports-url]: https://github.com/asottile/reorder-python-imports/
[pydantic-image]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json
[pydantic-url]: https://pydantic.dev
[pre-commit-image]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
[pre-commit-url]: https://github.com/pre-commit/pre-commit
[license-image]: https://img.shields.io/github/license/DARPAI/portal
[license-url]: https://opensource.org/licenses/MIT 
