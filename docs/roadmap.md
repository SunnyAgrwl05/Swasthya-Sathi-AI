# Project Roadmap

This roadmap organizes future work for Swasthya Sathi AI across product, AI, backend, frontend, testing, and deployment maturity.

## Completed Foundation

- FastAPI backend.
- React and Vite frontend.
- SQLite persistence.
- Worker listing and creation APIs.
- Attendance listing and update APIs.
- Attendance analytics summary endpoint.
- AI chat endpoint.
- Daily broadcast endpoint.
- Weekly insights endpoint.
- Dashboard cards, charts, worker table, chat panel, and report components.
- Backend test scaffold with Pytest.
- Frontend test scaffold with Vitest and Testing Library.
- Docker and deployment configuration.

## Near-Term Priorities

### Documentation

- Keep setup instructions aligned with actual repository files.
- Add screenshots for each major dashboard state.
- Document environment variables and deployment steps.
- Add example API requests and responses.

### Testing

- Add tests for attendance create and update behavior.
- Add tests for analytics summary calculations.
- Add tests for worker deletion behavior.
- Add agent-level tests with mocked model providers.
- Add frontend tests for dashboard loading, error, and empty states.

### Developer Experience

- Add `.env.example` files for backend and frontend.
- Add linting and formatting scripts.
- Add a root-level task runner or documented command matrix.
- Improve CI to run backend tests, frontend tests, and frontend build.

## Product Roadmap

### Authentication and Roles

- Add supervisor login.
- Add role-based access for supervisors, admins, and viewers.
- Restrict attendance mutation to authorized users.
- Add session and token security.

### Reporting

- Export attendance reports as CSV and PDF.
- Add date-range filters for analytics.
- Add centre-wise and role-wise reports.
- Add printable weekly supervisor summaries.

### Notifications

- Add configurable WhatsApp, SMS, or email provider integration.
- Track notification delivery status.
- Allow supervisors to preview messages before sending.
- Add reminder workflows for missing attendance.

### Multilingual Experience

- Improve Hindi and Hinglish prompt handling.
- Add language selection for dashboard labels.
- Add localized report templates.

## AI Roadmap

- Add mocked agent tests for deterministic CI.
- Add prompt evaluation cases for common supervisor workflows.
- Add safeguards for unsupported or ambiguous attendance actions.
- Improve explainability by showing action summaries.
- Add confidence or clarification prompts for fuzzy worker matches.
- Add human confirmation for high-impact operations.

## Backend Roadmap

- Move production deployments from SQLite to PostgreSQL.
- Add database migrations.
- Add pagination and filters to list endpoints.
- Add stricter CORS configuration.
- Add structured logging.
- Add rate limiting for AI and mutation endpoints.

## Frontend Roadmap

- Add loading and empty states for every dashboard section.
- Improve mobile dashboard layout.
- Add accessible labels and keyboard states.
- Add error recovery for failed API calls.
- Add report download buttons.
- Add worker detail pages.

## Deployment Roadmap

- Document Render backend deployment.
- Document Vercel frontend deployment.
- Add health checks for backend and frontend.
- Add production environment variable checklist.
- Add monitoring and alerting guidance.

## Long-Term Vision

Swasthya Sathi AI can evolve into a broader rural health operations cockpit that combines attendance, outreach tasks, worker performance insights, and supervisor communication into one transparent and auditable workflow.
