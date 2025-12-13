/**
 * Unit tests for AuthContext
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth, resetAuthState } from "../AuthContext";
import { mockFetch, mockFetchError, cleanupMocks } from "@/test-utils";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// Mock next/navigation
const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

describe("AuthContext", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    jest.clearAllMocks();
    mockPush.mockClear();
    resetAuthState();

    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  afterEach(() => {
    cleanupMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );

  describe("initial state", () => {
    it("should start unauthenticated", () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it("should turn off loading after hydration", async () => {
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });
    });

    it("should restore user from localStorage", async () => {
      const mockUser = {
        id: "123",
        email: "test@sdsu.edu",
        username: "testuser",
        role: "user" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      localStorage.setItem("auth_token", "test-token");
      localStorage.setItem("user", JSON.stringify(mockUser));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.user).toEqual(mockUser);
        expect(result.current.isAuthenticated).toBe(true);
      });
    });
  });

  describe("login", () => {
    it("should successfully login user", async () => {
      const mockResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: {
          id: "123",
          email: "test@sdsu.edu",
          username: "testuser",
          role: "user",
          is_verified: true,
          created_at: "2024-01-01T00:00:00Z",
        },
      };

      mockFetch(mockResponse);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login({
          username: "test@sdsu.edu",
          password: "password123",
        });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockResponse.user);
      expect(localStorage.getItem("auth_token")).toBe("test-token");
      expect(localStorage.getItem("user")).toBe(JSON.stringify(mockResponse.user));
    });

    it("should handle login failure", async () => {
      mockFetchError("Invalid credentials", 401);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await expect(
        act(async () => {
          await result.current.login({
            username: "wrong@sdsu.edu",
            password: "wrongpass",
          });
        })
      ).rejects.toThrow("Invalid credentials");

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
    });

    it("should clear existing query cache on login", async () => {
      const mockResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: {
          id: "123",
          email: "test@sdsu.edu",
          username: "testuser",
          role: "user",
          is_verified: true,
          created_at: "2024-01-01T00:00:00Z",
        },
      };

      mockFetch(mockResponse);

      const clearSpy = jest.spyOn(queryClient, "clear");

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.login({
          username: "test@sdsu.edu",
          password: "password123",
        });
      });

      expect(clearSpy).toHaveBeenCalled();
    });
  });

  describe("signup", () => {
    it("should successfully signup and auto-login", async () => {
      const signupResponse = {
        id: "123",
        email: "new@sdsu.edu",
        username: "newuser",
        role: "user",
        is_verified: false,
        created_at: "2024-01-01T00:00:00Z",
        verification_email_sent: true,
      };

      const loginResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: {
          id: "123",
          email: "new@sdsu.edu",
          username: "newuser",
          role: "user",
          is_verified: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      };

      // First call for signup, second for auto-login
      mockFetch(signupResponse);
      global.fetch = jest
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(signupResponse),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(loginResponse),
        }) as jest.Mock;

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.signup({
          email: "new@sdsu.edu",
          username: "newuser",
          password: "password123",
        });
      });

      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user?.username).toBe("newuser");
    });

    it("should store email_send_failed flag if email fails", async () => {
      const signupResponse = {
        id: "123",
        email: "new@sdsu.edu",
        username: "newuser",
        role: "user",
        is_verified: false,
        created_at: "2024-01-01T00:00:00Z",
        verification_email_sent: false,
      };

      const loginResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: signupResponse,
      };

      global.fetch = jest
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(signupResponse),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(loginResponse),
        }) as jest.Mock;

      const { result } = renderHook(() => useAuth(), { wrapper });

      await act(async () => {
        await result.current.signup({
          email: "new@sdsu.edu",
          username: "newuser",
          password: "password123",
        });
      });

      expect(sessionStorage.getItem("email_send_failed")).toBe("true");
    });
  });

  describe("logout", () => {
    it("should clear authentication and redirect to home", async () => {
      const mockUser = {
        id: "123",
        email: "test@sdsu.edu",
        username: "testuser",
        role: "user" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      localStorage.setItem("auth_token", "test-token");
      localStorage.setItem("user", JSON.stringify(mockUser));

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      act(() => {
        result.current.logout();
      });

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.user).toBeNull();
      expect(localStorage.getItem("auth_token")).toBeNull();
      expect(localStorage.getItem("user")).toBeNull();
      expect(mockPush).toHaveBeenCalledWith("/");
    });

    it("should cancel and clear queries on logout", async () => {
      const mockUser = {
        id: "123",
        email: "test@sdsu.edu",
        username: "testuser",
        role: "user" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      localStorage.setItem("auth_token", "test-token");
      localStorage.setItem("user", JSON.stringify(mockUser));

      const cancelQueriesSpy = jest.spyOn(queryClient, "cancelQueries");
      const clearSpy = jest.spyOn(queryClient, "clear");

      const { result } = renderHook(() => useAuth(), { wrapper });

      // Wait for hydration to complete first
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
      });

      act(() => {
        result.current.logout();
      });

      expect(cancelQueriesSpy).toHaveBeenCalled();
      expect(clearSpy).toHaveBeenCalled();
    });

    it("should clear banned_handler_called flag", () => {
      sessionStorage.setItem("banned_handler_called", "true");

      const { result } = renderHook(() => useAuth(), { wrapper });

      act(() => {
        result.current.logout();
      });

      expect(sessionStorage.getItem("banned_handler_called")).toBeNull();
    });
  });

  describe("error handling", () => {
    it("should throw error from useAuth when used outside provider", () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      expect(() => {
        renderHook(() => useAuth());
      }).toThrow("useAuth must be used within an AuthProvider");

      consoleSpy.mockRestore();
    });
  });
});
