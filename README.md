# Zrata Trader Backend

Zrata Trader is a backend service built with **FastAPI** and managed using **uv** for dependency management and virtual environments.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/algame-revamp/zrata-trader
cd zrata-trader
```

### 2. Install dependencies

We use uv to handle Python dependencies.

```bash
uv sync
```

This will create and manage a virtual environment automatically, based on `pyproject.toml` and `uv.lock`.

### 3. Run the FastAPI server

```bash
uv run uvicorn main:app --reload
```

By default, the server will start at:

- **Local**: http://localhost:8000

---

## 🛠 Development Notes

- Use `uv add <package>` to add new dependencies.
- Use `uv remove <package>` to remove dependencies.
- Run `uv sync` after updating dependencies.

Architecture:

```markdown
zrata-trader/
├── engine/
│ ├── **init**.py
│ ├── cache/
│ │ ├── **init**.py
│ │ ├── hasher.py # Creates unique IDs
│ │ ├── storage.py # Database operations
│ │ └── manager.py # Smart Filing Cabinet
│ ├── strategies/
│ │ ├── **init**.py
│ │ └── factory.py # Creates strategy classes
│ └── data/
│ ├── **init**.py
│ └── processor.py # Handles CSV data and other data
├── models/
│ ├── **init**.py
│ └── schemas.py # Data models
├── utils/
│ ├── **init**.py
│ └── helpers.py # Helper functions
├── storage/
│ └── .gitkeep # Database files go here (for future)
├── main.py # FastAPI app ( maybe as it gets complex we will change this)
├── pyproject.toml
└── requirements.txt
```

For production, you may run without `--reload`:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```
