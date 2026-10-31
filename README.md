# StockSense — Smart Inventory & Demand Prediction (Academic Prototype)

A simple Class 12 Python project showing stock management, sales, supplier records, low-stock indicators, and **transparent moving-average demand estimates**. Built with Streamlit + SQLite.

**Demo limitation:** Sample products and historical sales are fictional. The estimate is a simple 14-day average; it does not use machine learning, seasons, holidays, or lead times. It should not be used for real procurement decisions.

## Run on Windows (PowerShell)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open http://localhost:8501. Python 3.11 also works (`py -3.11`).

## Tests
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Live demo
1. Open **Overview** to view stock and low-stock alerts.
2. Add a product with a unique SKU in **Products**.
3. Record a sale and verify that stock reduces; attempt a larger-than-stock sale to show validation.
4. Receive new stock and verify that quantity increases.
5. View **Demand estimate**, its historical chart and suggested reorder quantity.

## Files
- `app.py`: Streamlit interface
- `stocksense/core.py`: SQLite schema, transactions, forecast formulas
- `tests/test_core.py`: automated unit tests
- `requirements.txt`: package requirements
- `stocksense.db`: locally created database (ignored by Git)

## Upload to GitHub Desktop
File → Add Local Repository → choose this extracted folder → **Create a repository here** (if prompted) → Commit → Publish Repository. Keep `.db` and `.venv` private/local; `.gitignore` excludes them.
