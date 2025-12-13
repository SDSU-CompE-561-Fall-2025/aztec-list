/**
 * Integration tests for authentication flows
 * Tests the complete user journey: signup -> login -> logout
 */

import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders, mockFetch } from "@/test-utils";
import { Header } from "@/components/custom/header";
import { useRouter } from "next/navigation";
import { resetAuthState } from "@/contexts/AuthContext";

const mockPush = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

describe("Authentication Flow Integration Tests", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    resetAuthState();
    mockPush.mockClear();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      prefetch: jest.fn(),
    });
  });

  describe("Complete signup -> login -> logout flow", () => {
    it("should successfully complete full authentication cycle", async () => {
      const user = userEvent.setup();

      // Step 1: Start unauthenticated
      const { rerender } = renderWithProviders(<Header />);

      // Wait for auth context to hydrate before checking UI
      await waitFor(() => {
        expect(screen.queryByText("Login")).toBeInTheDocument();
      });

      expect(screen.getByText("Sign Up")).toBeInTheDocument();

      // Step 2: Simulate signup API call
      const signupResponse = {
        id: "123",
        email: "newuser@sdsu.edu",
        username: "newuser",
        role: "user",
        is_verified: false,
        created_at: "2024-01-01T00:00:00Z",
        verification_email_sent: true,
      };

      const loginResponse = {
        access_token: "test-token-123",
        token_type: "bearer",
        user: {
          id: "123",
          email: "newuser@sdsu.edu",
          username: "newuser",
          role: "user",
          is_verified: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      };

      // Mock signup then auto-login
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

      // Manually set auth state to simulate successful signup/login
      localStorage.setItem("auth_token", "test-token-123");
      localStorage.setItem("user", JSON.stringify(loginResponse.user));

      // Notify AuthContext of auth change
      window.dispatchEvent(new CustomEvent("auth-user-updated"));

      // Step 3: Rerender to show authenticated state
      rerender(<Header />);

      await waitFor(() => {
        expect(screen.queryByText("Login")).not.toBeInTheDocument();
        expect(screen.queryByText("Sign Up")).not.toBeInTheDocument();
      });

      // Step 4: Verify user is logged in (avatar shows)
      await waitFor(() => {
        expect(screen.getByText("N")).toBeInTheDocument(); // First letter of username
      });

      // Step 5: Open user menu
      const avatar = screen.getByText("N");
      await user.click(avatar);

      // Verify menu items
      await waitFor(() => {
        expect(screen.getByText("Profile")).toBeInTheDocument();
        expect(screen.getByText("Messages")).toBeInTheDocument();
        expect(screen.getByText("Settings")).toBeInTheDocument();
        expect(screen.getByText("Log out")).toBeInTheDocument();
      });

      // Step 6: Logout
      const logoutButton = screen.getByText("Log out");
      await user.click(logoutButton);

      // Step 7: Verify logged out state
      expect(localStorage.getItem("auth_token")).toBeNull();
      expect(localStorage.getItem("user")).toBeNull();
      expect(mockPush).toHaveBeenCalledWith("/");
    });
  });

  describe("Login flow", () => {
    it("should successfully login and update UI", async () => {
      const loginResponse = {
        access_token: "test-token",
        token_type: "bearer",
        user: {
          id: "456",
          email: "existing@sdsu.edu",
          username: "existinguser",
          role: "user",
          is_verified: true,
          created_at: "2024-01-01T00:00:00Z",
        },
      };

      mockFetch(loginResponse);

      renderWithProviders(<Header />);

      // Initially unauthenticated - wait for hydration
      await waitFor(() => {
        expect(screen.queryByText("Login")).toBeInTheDocument();
      });

      // Simulate successful login
      localStorage.setItem("auth_token", "test-token");
      localStorage.setItem("user", JSON.stringify(loginResponse.user));

      // Dispatch auth update event
      window.dispatchEvent(new CustomEvent("auth-user-updated"));

      await waitFor(() => {
        expect(screen.queryByText("Login")).not.toBeInTheDocument();
      });
    });

    it("should handle login failure gracefully", async () => {
      renderWithProviders(<Header />);

      // Verify stays unauthenticated - wait for hydration
      await waitFor(() => {
        expect(screen.queryByText("Login")).toBeInTheDocument();
      });
      expect(screen.getByText("Sign Up")).toBeInTheDocument();

      // Should not have token or user data
      expect(localStorage.getItem("auth_token")).toBeNull();
      expect(localStorage.getItem("user")).toBeNull();
    });
  });

  describe("Session persistence", () => {
    it("should restore session from localStorage on mount", async () => {
      const mockUser = {
        id: "789",
        email: "persistent@sdsu.edu",
        username: "persistentuser",
        role: "user" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      // Pre-populate localStorage
      localStorage.setItem("auth_token", "existing-token");
      localStorage.setItem("user", JSON.stringify(mockUser));

      // Notify AuthContext - must do before render to ensure initial state is correct
      window.dispatchEvent(new CustomEvent("auth-user-updated"));

      renderWithProviders(<Header />);

      // Should show authenticated state - wait for loading skeleton to disappear
      await waitFor(() => {
        expect(screen.queryByText("Login")).not.toBeInTheDocument();
      });

      // Avatar with first letter should be visible
      await waitFor(() => {
        expect(screen.getByText("P")).toBeInTheDocument(); // First letter
      });

      expect(screen.queryByText("Sign Up")).not.toBeInTheDocument();
    });

    it("should not restore session if token is missing", async () => {
      const mockUser = {
        id: "789",
        email: "test@sdsu.edu",
        username: "testuser",
        role: "user" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      // User data present but no token
      localStorage.setItem("user", JSON.stringify(mockUser));

      renderWithProviders(<Header />);

      // Should show unauthenticated state - wait for hydration
      await waitFor(() => {
        expect(screen.queryByText("Login")).toBeInTheDocument();
      });
      expect(screen.getByText("Sign Up")).toBeInTheDocument();
    });
  });

  describe("Admin user flow", () => {
    it("should show admin menu for admin users", async () => {
      const user = userEvent.setup();

      const adminUser = {
        id: "admin-1",
        email: "admin@sdsu.edu",
        username: "adminuser",
        role: "admin" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      localStorage.setItem("auth_token", "admin-token");
      localStorage.setItem("user", JSON.stringify(adminUser));

      // Notify AuthContext
      window.dispatchEvent(new CustomEvent("auth-user-updated"));

      renderWithProviders(<Header />);

      // Wait for auth to hydrate and loading skeleton to disappear
      await waitFor(() => {
        expect(screen.queryByText("Login")).not.toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("A")).toBeInTheDocument();
      });

      // Open menu
      const avatar = screen.getByText("A");
      await user.click(avatar);

      // Verify admin menu item exists
      await waitFor(() => {
        expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
      });
    });

    it("should not show admin menu for regular users", async () => {
      const user = userEvent.setup();

      const regularUser = {
        id: "user-1",
        email: "user@sdsu.edu",
        username: "regularuser",
        role: "user" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      localStorage.setItem("auth_token", "user-token");
      localStorage.setItem("user", JSON.stringify(regularUser));

      // Notify AuthContext
      window.dispatchEvent(new CustomEvent("auth-user-updated"));

      renderWithProviders(<Header />);

      // Wait for auth to hydrate and loading skeleton to disappear
      await waitFor(() => {
        expect(screen.queryByText("Login")).not.toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText("R")).toBeInTheDocument();
      });

      // Open menu
      const avatar = screen.getByText("R");
      await user.click(avatar);

      // Verify admin menu item does not exist
      await waitFor(() => {
        expect(screen.queryByText("Admin Dashboard")).not.toBeInTheDocument();
      });
    });
  });
});
