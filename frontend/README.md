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
