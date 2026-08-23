# Contributing to Swasthya Sathi AI

Thank you for helping improve Swasthya Sathi AI. This project sits at the intersection of healthcare operations, AI-assisted workflows, and open-source education, so contributions should be clear, tested, and easy for maintainers to review.

## Contribution Principles

- Keep pull requests focused on one issue or improvement.
- Prefer small, reviewable changes over broad rewrites.
- Preserve the healthcare operations context of the project.
- Avoid committing secrets, API keys, database dumps, or local environment files.
- Update documentation when behavior, setup, or architecture changes.
- Add or update tests when code behavior changes.

## Local Development Setup

See [docs/setup.md](docs/setup.md) for the full setup guide.

Short version:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
uvicorn main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

On Windows PowerShell, activate the backend virtual environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Branch Workflow

1. Fork the repository.
2. Sync your fork with the upstream `main` branch.
3. Create a descriptive branch:

```bash
git checkout -b docs/research-ready-repo
```

4. Make the smallest complete change that solves the assigned issue.
5. Run relevant checks.
6. Open a pull request against the upstream `main` branch.

## Commit and PR Guidelines

Use clear commit messages:

```text
docs: add research methodology guide
fix: handle missing attendance summary data
test: cover worker listing endpoint
```

Every PR should include:

- Summary of the change.
- Linked issue, for example `Closes #15`.
- Tests or checks run.
- Screenshots for UI changes.
- Notes about any known limitations or follow-up work.

## Testing Checklist

Run the checks that apply to your change.

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

Documentation-only changes should still be reviewed for:

- Broken links.
- Accurate setup commands.
- Correct file paths.
- Clear grammar and formatting.

## Documentation Standards

- Use concise Markdown headings.
- Prefer code blocks for commands and configuration.
- Keep diagrams readable in plain text or Mermaid-compatible Markdown.
- Explain the reason behind workflows, not just the steps.
- If a feature depends on an external service, document the required environment variables.

## Security and Privacy

This project models healthcare operations data. Even demo data should be treated thoughtfully.

- Do not commit real patient, worker, phone, or facility data.
- Do not expose API keys in examples.
- Use placeholder values in documentation.
- Report security concerns privately to the maintainer when possible.

## Asking for Help

If setup fails or an issue is unclear, comment on the issue with:

- Your operating system.
- The command that failed.
- The exact error message.
- What you already tried.

Clear context helps maintainers and contributors unblock you faster.
