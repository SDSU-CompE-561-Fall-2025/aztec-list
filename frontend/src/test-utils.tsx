import React, { ReactElement } from "react";
import { render, RenderOptions } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/contexts/AuthContext";

/**
 * Create a new QueryClient for each test to ensure isolation
 */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Custom render function that wraps components with necessary providers
 */
interface AllTheProvidersProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
}

function AllTheProviders({ children, queryClient }: AllTheProvidersProps) {
  const client = queryClient || createTestQueryClient();

  return (
    <QueryClientProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  queryClient?: QueryClient;
}

/**
 * Custom render method that includes all providers
 */
export function renderWithProviders(
  ui: ReactElement,
  { queryClient, ...renderOptions }: CustomRenderOptions = {}
) {
  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders queryClient={queryClient}>{children}</AllTheProviders>
    ),
    ...renderOptions,
  });
}

/**
 * Mock fetch responses for testing
 */
export function mockFetch(response: unknown, options: { ok?: boolean; status?: number } = {}) {
  const { ok = true, status = 200 } = options;

  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok,
      status,
      json: () => Promise.resolve(response),
      text: () => Promise.resolve(JSON.stringify(response)),
      headers: new Headers(),
    })
  ) as jest.Mock;

  return global.fetch as jest.Mock;
}

/**
 * Mock fetch error for testing error handling
 */
export function mockFetchError(error: string, status = 400) {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: false,
      status,
      json: () => Promise.resolve({ detail: error }),
      text: () => Promise.resolve(JSON.stringify({ detail: error })),
      headers: new Headers(),
    })
  ) as jest.Mock;

  return global.fetch as jest.Mock;
}

/**
 * Mock fetch network failure
 */
export function mockFetchNetworkError() {
  global.fetch = jest.fn(() => Promise.reject(new Error("Network error"))) as jest.Mock;
  return global.fetch as jest.Mock;
}

/**
 * Clean up mocks after tests
 */
export function cleanupMocks() {
  jest.restoreAllMocks();
  localStorage.clear();
  sessionStorage.clear();
}

/**
 * Wait for async updates in tests
 */
export const waitFor = async (callback: () => void, timeout = 1000) => {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      callback();
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
  }
  callback(); // Final attempt that will throw if still failing
};

/**
 * Wait for AuthContext to finish hydrating from localStorage
 * This ensures isLoading becomes false before assertions
 */
export async function waitForAuthHydration() {
  // Wait a tick for useEffect to run and set isHydrated to true
  await new Promise((resolve) => setTimeout(resolve, 0));
}

// Re-export everything from React Testing Library
export * from "@testing-library/react";
export { default as userEvent } from "@testing-library/user-event";
