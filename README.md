# ExitBot - AI-powered Exit Interview Assistant

ExitBot is an application that uses AI to conduct and analyze exit interviews, helping organizations understand why employees leave and how to improve retention.

## Features

- Conduct AI-powered exit interviews
- Analyze sentiment in employee responses
- Generate reports and insights
- User-friendly API for integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/exitbot.git
cd exitbot
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Configure your environment:
   - Copy `.env.example` to `.env`
   - Update the configuration values, especially:
     - `SECRET_KEY`: Generate a secure random string
     - `GROQ_API_KEY`: Add your Groq API key for LLM integration

## Running the Application

To start the development server:

```bash
python -m exitbot.run
```

The API will be available at http://localhost:8000.

API documentation can be accessed at:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Project Structure

```
exitbot/
├── app/
│   ├── api/        # API endpoints
│   ├── core/       # Core functionality and settings
│   ├── db/         # Database models and operations
│   ├── llm/        # LLM integration
│   ├── schemas/    # Pydantic models for validation
│   └── services/   # Business logic
├── tests/          # Test suite
└── run.py          # Application entry point
```

## Development

To initialize the database:

```bash
python -m exitbot.app.db.init
```

To run tests:

```bash
pytest
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 