/**
 * Unit tests for Header component
 */

import { screen, fireEvent, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Header } from "../header";
import { renderWithProviders } from "@/test-utils";
import { useRouter, usePathname } from "next/navigation";
import { resetAuthState } from "@/contexts/AuthContext";

// Mock next/navigation
const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockPathname = jest.fn(() => "/");

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
  useSearchParams: () => new URLSearchParams(),
}));

describe("Header Component", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    resetAuthState();
    mockPush.mockClear();
    mockReplace.mockClear();
    mockPathname.mockReturnValue("/");
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
      prefetch: jest.fn(),
    });
    (usePathname as jest.Mock).mockImplementation(mockPathname);

    localStorage.clear();
  });

  describe("rendering", () => {
    it("should render logo", () => {
      renderWithProviders(<Header />);
      expect(screen.getByText("Aztec")).toBeInTheDocument();
      expect(screen.getByText("List")).toBeInTheDocument();
    });

    it("should render search bar", () => {
      renderWithProviders(<Header />);
      const searchInput = screen.getByPlaceholderText("Search...");
      expect(searchInput).toBeInTheDocument();
    });

    it("should render login and signup buttons when not authenticated", () => {
      renderWithProviders(<Header />);
      expect(screen.getByText("Login")).toBeInTheDocument();
      expect(screen.getByText("Sign Up")).toBeInTheDocument();
    });

    it("should render user avatar when authenticated", async () => {
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

      renderWithProviders(<Header />);

      // Wait for component to mount and hydrate
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
        window.dispatchEvent(new CustomEvent("auth-user-updated"));
      });

      // Avatar should show first letter of username after hydration
      await waitFor(
        () => {
          expect(screen.getByText("T")).toBeInTheDocument();
        },
        { timeout: 5000 }
      );
    });
  });

  describe("search functionality", () => {
    it("should navigate to listings with search query on submit", () => {
      renderWithProviders(<Header />);

      const searchInput = screen.getByPlaceholderText("Search...");
      fireEvent.change(searchInput, { target: { value: "laptop" } });
      fireEvent.submit(searchInput);

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("/listings?q=laptop&sort=recent")
      );
    });

    it("should navigate to listings without query if search is empty", () => {
      renderWithProviders(<Header />);

      const searchInput = screen.getByPlaceholderText("Search...");
      fireEvent.submit(searchInput);

      expect(mockPush).toHaveBeenCalledWith(expect.stringContaining("/listings?sort=recent"));
      expect(mockPush).not.toHaveBeenCalledWith(expect.stringContaining("q="));
    });

    it("should trim whitespace from search query", () => {
      renderWithProviders(<Header />);

      const searchInput = screen.getByPlaceholderText("Search...");
      fireEvent.change(searchInput, { target: { value: "  laptop  " } });
      fireEvent.submit(searchInput);

      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining("/listings?q=laptop&sort=recent")
      );
    });

    it("should use replace instead of push when already on listings page", () => {
      mockPathname.mockReturnValue("/listings");

      renderWithProviders(<Header />);

      const searchInput = screen.getByPlaceholderText("Search...");
      fireEvent.change(searchInput, { target: { value: "textbook" } });
      fireEvent.submit(searchInput);

      expect(mockReplace).toHaveBeenCalledWith(
        expect.stringContaining("/listings?q=textbook&sort=recent")
      );
      expect(mockPush).not.toHaveBeenCalled();
    });

    it("should encode special characters in search query", () => {
      renderWithProviders(<Header />);

      const searchInput = screen.getByPlaceholderText("Search...");
      fireEvent.change(searchInput, { target: { value: "laptop & phone" } });
      fireEvent.submit(searchInput);

      expect(mockPush).toHaveBeenCalledWith(expect.stringContaining("q=laptop%20%26%20phone"));
    });
  });

  describe("authentication UI", () => {
    it("should show loading placeholders during auth check", () => {
      // This is handled by isLoading state in AuthContext
      renderWithProviders(<Header />);
      // Initially shows loading state before hydration completes
    });

    it("should show user menu when authenticated", async () => {
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

      renderWithProviders(<Header />);

      // Wait for component to mount and hydrate
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
        window.dispatchEvent(new CustomEvent("auth-user-updated"));
      });

      // Wait for hydration and avatar to appear
      await waitFor(
        () => {
          expect(screen.getByText("T")).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      const avatar = screen.getByText("T").closest("span");
      expect(avatar).toBeInTheDocument();
    });

    it("should show admin menu item for admin users", async () => {
      const mockAdminUser = {
        id: "123",
        email: "admin@sdsu.edu",
        username: "adminuser",
        role: "admin" as const,
        is_verified: true,
        created_at: "2024-01-01T00:00:00Z",
      };

      localStorage.setItem("auth_token", "test-token");
      localStorage.setItem("user", JSON.stringify(mockAdminUser));

      renderWithProviders(<Header />);

      // Wait for component to mount and hydrate
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
        window.dispatchEvent(new CustomEvent("auth-user-updated"));
      });

      // Wait for hydration and avatar to appear
      await waitFor(
        () => {
          expect(screen.getByText("A")).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Click avatar to open menu
      const user = userEvent.setup();
      const avatar = screen.getByText("A");
      await user.click(avatar);

      // Wait for dropdown menu to appear
      await waitFor(() => {
        expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
      });
    });
  });

  describe("theme switcher", () => {
    it("should render theme switcher", () => {
      const { container } = renderWithProviders(<Header />);
      // ThemeSwitcher component should be rendered
      // Exact assertion depends on ThemeSwitcher implementation
      expect(container.querySelector("button")).toBeInTheDocument();
    });
  });
});
