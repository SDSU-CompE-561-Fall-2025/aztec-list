# Frontend

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

See the main [README.md](../README.md#frontend-quickstart) for initial setup instructions.

## Environment Configuration

Environment variables are configured in `.env.local` in the **frontend/** directory.

To set up:

```bash
# From frontend/ directory
cp .env.example .env.local

# Edit .env.local to configure API URLs (optional for local development)
```

**Key Configuration Options:**

- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL including version path (default: http://127.0.0.1:8000/api/v1)
- `NEXT_PUBLIC_STATIC_BASE_URL` - Static files/images URL (default: http://127.0.0.1:8000)
- `NEXT_PUBLIC_APP_NAME` - Application name (default: "Aztec List")

See `.env.example` for all available options and production deployment notes.

## Development

```bash
# Start the dev server
bun dev
# or: npm run dev | yarn dev | pnpm dev

# Open http://localhost:3000
```

## Code Quality Commands

```bash
# Format all files
bun run format

# Check if files are formatted correctly (no changes)
bun run format:check

# Lint code
bun run lint

# Lint and auto-fix issues
bun run lint:fix
```

**Note:** Pre-commit hooks automatically run ESLint and Prettier on staged files when you commit. See the main [README.md](../README.md#code-quality--pre-commit-hooks) for details.

## Testing

### E2E Tests with Playwright

End-to-end tests are located in `tests/e2e/` and use [Playwright](https://playwright.dev/) for browser automation.

#### Running Tests

```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/auth-login.spec.ts

# Run tests sequentially (useful for debugging)
npx playwright test --workers=1

# Run tests in headed mode (see the browser)
npx playwright test --headed

# Run tests in UI mode (interactive debugging)
npx playwright test --ui

# View last test report
npx playwright show-report
```

#### Test Structure

E2E tests are organized by feature:

**Authentication:**

- `auth-login.spec.ts` - Login functionality
- `auth-signup.spec.ts` - User registration
- `auth-logout.spec.ts` - Logout functionality

**Listings:**

- `listings-browse.spec.ts` - Browse and search listings
- `listings-create.spec.ts` - Create new listings
- `listings-detail.spec.ts` - View listing details
- `listings-edit-delete.spec.ts` - Edit and delete listings

**User Profile:**

- `profile-management.spec.ts` - User profile and settings

**Admin Dashboard:**

- `admin-actions.spec.ts` - View admin actions history, revoke actions
- `admin-moderation.spec.ts` - Issue strikes, ban users, remove listings
- `admin-access-control.spec.ts` - Admin route protection and authorization

**Utilities:**

- `helpers/test-helpers.ts` - Shared test utilities

> **Note:** Many admin tests are currently skipped (marked with `test.skip()`) as they require the ability to create admin users in the test environment. These serve as templates for future implementation when admin user test infrastructure is available.

#### Test Helpers

The `helpers/test-helpers.ts` file provides utilities for:

- **Test Data Generation**: `generateTestEmail()`, `generateUsername()`, `generatePassword()`
- **Authentication**: `isUserLoggedIn()`, `isUserLoggedOut()`, `logout()`
- **State Verification**: `hasAuthToken()`

Example usage:

```typescript
import { generateTestEmail, generatePassword } from "./helpers/test-helpers";

const email = generateTestEmail();
const password = generatePassword();
```

#### Configuration

Tests are configured in `playwright.config.ts`:

- **Automatic Server Startup**: Both backend (FastAPI) and frontend (Next.js) start automatically before tests run
- **Base URL**: `http://localhost:3000` (configurable via `PLAYWRIGHT_BASE_URL`)
- **Test Directory**: `./tests/e2e`
- **Browser**: Chromium (Firefox and WebKit available but commented out)
- **Retries**: 2 retries on CI, 0 locally
- **Screenshots/Videos**: Captured on failure for debugging

#### CI vs Local Behavior

- **CI**: Runs sequentially (`workers: 1`), includes GitHub reporter
- **Local**: Runs in parallel for speed, reuses existing dev servers

#### Best Practices

- Each test should be independent and not rely on other tests
- Use test helpers for common operations (login, data generation)
- Tests automatically clean up by creating unique users/data per test
- Use descriptive test names that explain what is being tested

## Build

```bash
# Create production build
bun run build

# Start production server
bun run start
```

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
