/**
 * Authentication API functions.
 */

import { API_BASE_URL } from "@/lib/constants";
import { AuthToken, LoginCredentials, SignupData, User } from "@/types/auth";

/**
 * Custom event name for auth user updates
 */
export const AUTH_USER_UPDATED_EVENT = "auth-user-updated" as const;

/**
 * Authenticate user and return access token.
 *
 * @param credentials - User login credentials (username/email and password)
 * @returns AuthToken with access token and user data
 * @throws Error if authentication fails
 */
export const login = async (credentials: LoginCredentials): Promise<AuthToken> => {
  const formData = new URLSearchParams();
  formData.append("username", credentials.username);
  formData.append("password", credentials.password);

  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Authentication failed" }));
    throw new Error(errorData.detail || "Invalid credentials");
  }

  const data = await res.json();
  return data as AuthToken;
};

/**
 * Register a new user account.
 *
 * @param signupData - New user registration data
 * @returns Created user's public information with email sending status
 * @throws Error if registration fails
 */
export const signup = async (
  signupData: SignupData
): Promise<User & { verification_email_sent?: boolean }> => {
  const res = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(signupData),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(errorData.detail || "Could not create account");
  }

  const data = await res.json();
  return data;
};

/**
 * Store authentication token in localStorage.
 *
 * @param token - JWT access token
 */
export const setAuthToken = (token: string): void => {
  if (typeof window !== "undefined") {
    localStorage.setItem("auth_token", token);
  }
};

/**
 * Retrieve authentication token from localStorage.
 *
 * @returns Stored token or null if not found
 */
export const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("auth_token");
  }
  return null;
};

/**
 * Remove authentication token from localStorage.
 */
export const removeAuthToken = (): void => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("auth_token");
  }
};

/**
 * Store user data in localStorage.
 *
 * @param user - User object to store
 */
export const setStoredUser = (user: User): void => {
  if (typeof window !== "undefined") {
    localStorage.setItem("user", JSON.stringify(user));
    // Dispatch custom event to notify AuthContext of user update
    window.dispatchEvent(new CustomEvent(AUTH_USER_UPDATED_EVENT));
  }
};

/**
 * Retrieve user data from localStorage.
 *
 * @returns Stored user or null if not found
 */
export const getStoredUser = (): User | null => {
  if (typeof window !== "undefined") {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        return JSON.parse(userStr) as User;
      } catch {
        return null;
      }
    }
  }
  return null;
};

/**
 * Remove user data from localStorage.
 */
export const removeStoredUser = (): void => {
  if (typeof window !== "undefined") {
    localStorage.removeItem("user");
  }
};

/**
 * Change the current user's password.
 *
 * @param currentPassword - Current password for verification
 * @param newPassword - New password to set
 * @throws Error if password change fails
 */
export const changePassword = async (
  currentPassword: string,
  newPassword: string
): Promise<void> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const res = await fetch(`${API_BASE_URL}/users/me/password`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Password change failed" }));
    throw new Error(errorData.detail || "Could not change password");
  }
};

/**
 * Refresh current user data from the server and update localStorage.
 * Call this after actions that modify user state (email verification, profile updates, etc.)
 *
 * @throws Error if not authenticated or fetch fails
 */
export const refreshCurrentUser = async (): Promise<User> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const res = await fetch(`${API_BASE_URL}/users/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error("Failed to refresh user data");
  }

  const user = (await res.json()) as User;
  setStoredUser(user);
  return user;
};
