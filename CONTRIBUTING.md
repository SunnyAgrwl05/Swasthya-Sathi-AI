# Contributing to Swasthya Sathi AI

Thank you for your interest in contributing! This project is an AI-powered
healthcare assistant with a FastAPI backend and a React frontend. The guide
below helps you set up, test, and submit changes.

## Getting started

1. **Fork** this repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/Swasthya-Sathi-AI.git
   cd Swasthya-Sathi-AI
   ```

2. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up the backend**:

   ```bash
   cd backend
   cp .env.example .env
   pip install -r requirements.txt
   python seed.py
   uvicorn main:app --reload
   ```

4. **Set up the frontend** (in a second terminal):

   ```bash
   cd frontend
   cp .env.example .env
   npm install
   npm run dev
   ```

   The app runs at <http://localhost:5173>.

## Running tests

Backend tests use `pytest`:

```bash
cd backend
pytest
```

GitHub Actions runs the backend tests automatically on every push and pull
request — make sure they pass locally before submitting.

## Making changes

- Keep each pull request focused on one problem or feature.
- Describe what changed, why, and how you tested it in the PR description.
- Follow the existing code style in the file you are editing.
- Do not commit real secrets, `.env` files, or local data — `.env` is
  gitignored; only `.env.example` is tracked.

## Submitting a pull request

1. Push your branch to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a pull request against the `main` branch with a clear title and
   description.
3. Link any related issue (`Closes #<issue>`).

## Reporting issues

- Search existing issues first to avoid duplicates.
- Include the steps to reproduce, expected behaviour, actual behaviour, and
  your environment (OS, Python/Node versions).

## Code of conduct

Be respectful and constructive. Harassment or discrimination of any kind is
not tolerated. See the project's `CODE_OF_CONDUCT.md` (if present) for the
full text.
