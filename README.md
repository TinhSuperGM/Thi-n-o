# Thiên Đạo

## Backend
- `main.py`, `store.py`, `logic.py`
- `requirements.txt`
- `runtime.txt`

## Bot UI
- `bot_service/main.py`
- `bot_service/api.py`
- `bot_service/requirements.txt`

## Run backend locally
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Run bot locally
```bash
cd bot_service
pip install -r requirements.txt
export DISCORD_TOKEN="..."
export API_BASE_URL="http://127.0.0.1:8000"
python main.py
```
