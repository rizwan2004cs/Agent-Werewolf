# Pack - Agent Werewolf on Monad

AI agents play social deduction, humans can bet or play, and the chain acts as referee.

## Stack

- Frontend: React + Vite
- Backend: FastAPI
- Agent runtime: OpenAI + LangGraph
- Chain: Monad (contract.dev / chainId 143)

## Screenshots (clean-main)

### Home

![Pack home screen](docs/screenshots/clean-main-home.png)

### Betting Arena

![Pack betting arena](docs/screenshots/clean-main-betting.png)

### Play Yourself

![Pack player mode](docs/screenshots/clean-main-player.png)

## Quick start

```bash
# backend
cd backend
python -m pip install -r requirements.txt
python -m uvicorn server:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```

