
# Tri Sprint Master V10 — Perfect

## Lancer (local)
pip install streamlit pandas python-dateutil ics
streamlit run app.py

## CLI (offline)
python cli.py --date 2026-03-16 --fatigue 7 --export md > semaine.md

## Docker
docker build -t tri-master .
docker run -p 8501:8501 tri-master

## Tests
pip install pytest
pytest -q
