# Contributing to Swasthya Sathi AI

Thank you for your interest in contributing to **Swasthya Sathi AI**! This project operates at the intersection of rural public health, workforce intelligence, and autonomous AI agents. We welcome contributions from developers, researchers, designers, and healthcare enthusiasts worldwide.

Please take a few moments to review these guidelines before getting started.

---

## Code of Conduct

All contributors and maintainers are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand the community standards we uphold.

---

## Ways to Contribute

You can contribute to Swasthya Sathi AI in multiple ways:

1. **Reporting Bugs**: Found a bug or glitch? Open an issue on GitHub with steps to reproduce.
2. **Suggesting Enhancements**: Have ideas for new agent tools, charts, or public health metrics? Share them in GitHub Discussions or an issue.
3. **Submitting Pull Requests**: Fix a bug, add a feature, or improve documentation.
4. **Writing Documentation**: Help clarify setup guides, API specifications, or translation guides.
5. **Testing & QA**: Add unit or integration tests for backend endpoints and frontend components.

---

## Local Development Quickstart

For full setup instructions, read [docs/setup.md](docs/setup.md).

### 1. Fork & Clone
Fork the repository on GitHub and clone your fork locally:
```bash
git clone https://github.com/<your-username>/Swasthya-Sathi-AI.git
cd Swasthya-Sathi-AI
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
# .\.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Branching & Git Workflow

We follow standard GitHub Flow:

1. Keep your fork's `main` branch synced with upstream:
   ```bash
   git remote add upstream https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI.git
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. Create a focused, descriptive feature branch:
   ```bash
   git checkout -b <type>/<short-description>
   ```

   **Branch prefixes**:
   * `feat/` — New feature or capability (e.g. `feat/whatsapp-broadcast-channel`)
   * `fix/` — Bug fix (e.g. `fix/pdf-unicode-text-rendering`)
   * `docs/` — Documentation improvements (e.g. `docs/api-reference-guide`)
   * `test/` — Adding or improving tests (e.g. `test/worker-analytics-coverage`)
   * `refactor/` — Code refactoring without behavioral changes

3. Keep commits atomic, cohesive, and clearly documented.

---

## Commit Guidelines

We recommend using **Conventional Commits** syntax:

```text
<type>(<scope>): <short description in imperative mood>

[optional body]
[optional footer / issue reference]
```

**Examples**:
* `feat(agent): add attendance streak calculation tool`
* `fix(pdf): embed Noto Sans Devanagari font to prevent Unicode corruption`
* `docs(readme): add interactive architecture sequence diagram`
* `test(backend): add test cases for worker deletion endpoint`

---

## Coding Standards

### Backend (Python / FastAPI)
* **Code Style**: Adhere to PEP 8.
* **Linter**: We use [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting:
  ```bash
  cd backend
  ruff check .
  ruff check --fix .
  ```
* **Type Annotations**: Use Python standard type hints (`int`, `str`, `list[schemas.WorkerOut]`).
* **Dependency Injection**: Follow FastAPI idiomatic dependency patterns (`db: Session = Depends(get_db)`).

### Frontend (React / Vite)
* **Code Style**: Modern functional React with Hooks (`useState`, `useEffect`, `useMemo`, `useRef`).
* **Linter**: We use ESLint with Flat Config (`eslint.config.js`):
  ```bash
  cd frontend
  npm run lint
  ```
* **Styling**: Tailwind CSS utility classes; keep color variables aligned with design tokens (`pulse`, `line`, `panel`).
* **Components**: Place reusable visual components in `frontend/src/components/` and utility helpers in `frontend/src/utils/`.

---

## Testing Checklist

Before opening a pull request, verify that all automated checks pass locally:

### 1. Backend Tests & Lint
```bash
cd backend
pytest -v
ruff check .
python -m compileall -q .
```

### 2. Frontend Tests & Build
```bash
cd frontend
npm test
npm run lint
npm run build
```

---

## Pull Request Submission Process

1. Push your branch to your GitHub fork:
   ```bash
   git push origin <your-branch-name>
   ```
2. Navigate to [SunnyAgrwl05/Swasthya-Sathi-AI](https://github.com/SunnyAgrwl05/Swasthya-Sathi-AI) and click **New Pull Request**.
3. Fill in the PR description template:
   * **Summary**: Clear explanation of what was changed and why.
   * **Linked Issue**: E.g., `Closes #12` or `Fixes #34`.
   * **Verification**: List of tests and commands run.
   * **Screenshots**: Include before/after images for UI changes.
4. Respond to code review feedback constructively.

---

## Data Privacy & Healthcare Ethics

This project models public health operational workflows for community healthcare workers (ASHA, ANM, Anganwadi).

* **Never commit real identifiable healthcare data**, patient information, or real worker contact details.
* Only use synthetic names, generic phone numbers (e.g. `+91 98765 00000`), and fictional health centre identifiers in tests and sample data.
* Never commit secrets, `.env` files, or API credentials.

---

## Community & Questions

Need help or want to bounce an idea off the maintainers?
* Open an issue on GitHub.
* Connect with the maintainer **Sunny Kumar**:
  * [GitHub Profile](https://github.com/SunnyAgrwl05)
  * [LinkedIn](https://www.linkedin.com/in/sunny-kumar-a06484297)
