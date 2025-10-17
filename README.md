# Aztec List

## Overview
Aztec List is an OfferUp-style marketplace for college students. Students can post items with photos and descriptions, browse/search listings, and (in later iterations) coordinate sales via messaging. Prices are typically lower than MSRP.

## Requirements
- [uv](https://docs.astral.sh/uv/) installed
- Python **3.13** (recommended). `uv python install` will fetch it for you.

## Quickstart
```bash
# 1) Clone
git clone https://github.com/SDSU-CompE-561-Fall-2025/aztec-list.git
cd aztec-list

# 2) Install Python + sync deps from pyproject/uv.lock
uv python install
uv sync

# 3) (optional) Install Git hooks (ruff, EOF/line-endings, etc.)
uv run pre-commit install

# 4) Run the API (dev)
uv run fastapi dev src/app/main.py
```
**Notes**:
- Open http://127.0.0.1:8000/docs for Swagger UI
- Run `uv run uvicorn --app-dir src app.main:app --reload` to start the app without FastAPI dev wrapper
