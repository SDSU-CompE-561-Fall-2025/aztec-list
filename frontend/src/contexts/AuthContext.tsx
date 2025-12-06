"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import {
  login as apiLogin,
  signup as apiSignup,
  setAuthToken,
  getAuthToken,
  removeAuthToken,
  setStoredUser,
  getStoredUser,
  removeStoredUser,
} from "@/lib/auth";
import { AuthContextType, LoginCredentials, SignupData, User } from "@/types/auth";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Authentication provider component.
 * Manages user authentication state and provides auth methods.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize state from localStorage on mount
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window !== "undefined") {
      const token = getAuthToken();
      const storedUser = getStoredUser();
      return token && storedUser ? storedUser : null;
    }
    return null;
  });
  const [isLoading] = useState(false);
  const router = useRouter();

  /**
   * Authenticate user with credentials.
   */
  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const authToken = await apiLogin(credentials);

      // Store token and user data
      setAuthToken(authToken.access_token);
      setStoredUser(authToken.user);
      setUser(authToken.user);

      // Don't redirect here - let the calling component handle navigation
    } catch (error) {
      // Re-throw to allow component to handle the error
      throw error;
    }
  };

  /**
   * Register a new user and log them in.
   */
  const signup = async (signupData: SignupData): Promise<void> => {
    try {
      // First create the account
      await apiSignup(signupData);

      // Then automatically log them in
      await login({
        username: signupData.email, // Use email for login
        password: signupData.password,
      });
    } catch (error) {
      throw error;
    }
  };

  /**
   * Log out the current user.
   */
  const logout = (): void => {
    removeAuthToken();
    removeStoredUser();
    setUser(null);
    router.push("/");
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    signup,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access authentication context.
 * Must be used within an AuthProvider.
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
