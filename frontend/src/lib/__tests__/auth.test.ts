/**
 * Unit tests for authentication functions
 */

import {
  login,
  signup,
  setAuthToken,
  getAuthToken,
  removeAuthToken,
  setStoredUser,
  getStoredUser,
  removeStoredUser,
  changePassword,
  refreshCurrentUser,
  AUTH_USER_UPDATED_EVENT,
} from "../auth";
import { mockFetch, mockFetchError, cleanupMocks } from "@/test-utils";

describe("auth.ts", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  afterEach(() => {
    cleanupMocks();
  });

  describe("login", () => {
    it("should successfully login with valid credentials", async () => {
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

      const result = await login({
        username: "test@sdsu.edu",
        password: "password123",
      });

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/auth/login"),
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        })
      );
    });

    it("should throw error on invalid credentials", async () => {
      mockFetchError("Invalid credentials", 401);

      await expect(
        login({
          username: "wrong@sdsu.edu",
          password: "wrongpass",
        })
      ).rejects.toThrow("Invalid credentials");
    });

    it("should throw error on network failure", async () => {
      global.fetch = jest.fn(() => Promise.reject(new Error("Network error")));

      await expect(
        login({
          username: "test@sdsu.edu",
          password: "password123",
        })
      ).rejects.toThrow("Network error");
    });
  });

  describe("signup", () => {
    it("should successfully register a new user", async () => {
      const mockResponse = {
        id: "123",
        email: "newuser@sdsu.edu",
        username: "newuser",
        role: "user",
        is_verified: false,
        created_at: "2024-01-01T00:00:00Z",
        verification_email_sent: true,
      };

      mockFetch(mockResponse);

      const result = await signup({
        email: "newuser@sdsu.edu",
        username: "newuser",
        password: "password123",
      });

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/auth/signup"),
        expect.objectContaining({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        })
      );
    });

    it("should throw error if email already registered", async () => {
      mockFetchError("Email already registered", 400);

      await expect(
        signup({
          email: "existing@sdsu.edu",
          username: "newuser",
          password: "password123",
        })
      ).rejects.toThrow("Email already registered");
    });
  });

  describe("token management", () => {
    it("should store and retrieve auth token", () => {
      const token = "test-token-123";
      setAuthToken(token);
      expect(getAuthToken()).toBe(token);
    });

    it("should remove auth token", () => {
      setAuthToken("test-token");
      removeAuthToken();
      expect(getAuthToken()).toBeNull();
    });

    it("should return null if no token exists", () => {
      expect(getAuthToken()).toBeNull();
    });
  });

  describe("user storage", () => {
    const mockUser = {
      id: "123",
      email: "test@sdsu.edu",
      username: "testuser",
      role: "user" as const,
      is_verified: true,
      created_at: "2024-01-01T00:00:00Z",
    };

    it("should store and retrieve user data", () => {
      setStoredUser(mockUser);
      const retrieved = getStoredUser();
      expect(retrieved).toEqual(mockUser);
    });

    it("should dispatch custom event when user is stored", () => {
      const eventListener = jest.fn();
      window.addEventListener(AUTH_USER_UPDATED_EVENT, eventListener);

      setStoredUser(mockUser);

      expect(eventListener).toHaveBeenCalled();
      window.removeEventListener(AUTH_USER_UPDATED_EVENT, eventListener);
    });

    it("should remove user data", () => {
      setStoredUser(mockUser);
      removeStoredUser();
      expect(getStoredUser()).toBeNull();
    });

    it("should return null if no user exists", () => {
      expect(getStoredUser()).toBeNull();
    });

    it("should handle invalid JSON in localStorage", () => {
      localStorage.setItem("user", "invalid-json");
      expect(getStoredUser()).toBeNull();
    });
  });

  describe("changePassword", () => {
    beforeEach(() => {
      setAuthToken("test-token");
    });

    it("should successfully change password", async () => {
      mockFetch({ message: "Password changed successfully" });

      await changePassword("oldPassword", "newPassword123");

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/users/me/password"),
        expect.objectContaining({
          method: "PATCH",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            Authorization: "Bearer test-token",
          }),
        })
      );
    });

    it("should throw error if not authenticated", async () => {
      removeAuthToken();

      await expect(changePassword("old", "new")).rejects.toThrow("Not authenticated");
    });

    it("should throw error if current password is incorrect", async () => {
      mockFetchError("Current password is incorrect", 401);

      await expect(changePassword("wrongPass", "newPass")).rejects.toThrow(
        "Current password is incorrect"
      );
    });
  });

  describe("refreshCurrentUser", () => {
    const mockUser = {
      id: "123",
      email: "test@sdsu.edu",
      username: "testuser",
      role: "user" as const,
      is_verified: true,
      created_at: "2024-01-01T00:00:00Z",
    };

    beforeEach(() => {
      setAuthToken("test-token");
    });

    it("should fetch and update user data", async () => {
      mockFetch(mockUser);

      const result = await refreshCurrentUser();

      expect(result).toEqual(mockUser);
      expect(getStoredUser()).toEqual(mockUser);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/users/me"),
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
          }),
        })
      );
    });

    it("should throw error if not authenticated", async () => {
      removeAuthToken();

      await expect(refreshCurrentUser()).rejects.toThrow("Not authenticated");
    });

    it("should throw error if fetch fails", async () => {
      mockFetchError("User not found", 404);

      await expect(refreshCurrentUser()).rejects.toThrow("Failed to refresh user data");
    });
  });
});
