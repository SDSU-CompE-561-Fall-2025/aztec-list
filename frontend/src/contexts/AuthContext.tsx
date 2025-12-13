"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useSyncExternalStore,
  ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  login as apiLogin,
  signup as apiSignup,
  setAuthToken,
  getAuthToken,
  removeAuthToken,
  setStoredUser,
  getStoredUser,
  removeStoredUser,
  AUTH_USER_UPDATED_EVENT,
} from "@/lib/auth";
import { AuthContextType, LoginCredentials, SignupData, User } from "@/types/auth";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Prevents infinite loops from frequent snapshot recalculations
let cachedAuthSnapshot: User | null = null;
let isSnapshotInitialized = false;

let authListeners: Array<() => void> = [];
function subscribeToAuth(callback: () => void) {
  authListeners.push(callback);
  return () => {
    authListeners = authListeners.filter((l) => l !== callback);
  };
}

function notifyAuthListeners() {
  isSnapshotInitialized = false;
  authListeners.forEach((listener) => listener());
}

function getAuthSnapshot(): User | null {
  if (isSnapshotInitialized) {
    return cachedAuthSnapshot;
  }

  const token = getAuthToken();
  const storedUser = getStoredUser();
  cachedAuthSnapshot = token && storedUser ? storedUser : null;
  isSnapshotInitialized = true;

  return cachedAuthSnapshot;
}

function getServerAuthSnapshot(): User | null {
  return null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const user = useSyncExternalStore(subscribeToAuth, getAuthSnapshot, getServerAuthSnapshot);

  const [isLoading, setIsLoading] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  useEffect(() => {
    setIsHydrated(true);

    // Listen for custom auth-user-updated events
    const handleAuthUpdate = () => {
      notifyAuthListeners();
    };

    window.addEventListener(AUTH_USER_UPDATED_EVENT, handleAuthUpdate);

    return () => {
      window.removeEventListener(AUTH_USER_UPDATED_EVENT, handleAuthUpdate);
    };
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      const authToken = await apiLogin(credentials);

      setAuthToken(authToken.access_token);
      setStoredUser(authToken.user);

      // Clear cached data from any previous session
      queryClient.clear();

      notifyAuthListeners();
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (signupData: SignupData): Promise<void> => {
    try {
      setIsLoading(true);
      const result = await apiSignup(signupData);

      // Store email sending status in sessionStorage for success page
      if (result.verification_email_sent === false) {
        sessionStorage.setItem("email_send_failed", "true");
      }

      await login({
        username: signupData.email,
        password: signupData.password,
      });
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (): void => {
    removeAuthToken();
    removeStoredUser();

    // Stop inflight queries, then clear cache to prevent leakage between users
    queryClient.cancelQueries();
    queryClient.clear();

    // Clear banned handler flag to allow it to trigger for a different account
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem("banned_handler_called");
    }

    notifyAuthListeners();

    router.push("/");
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading: isLoading || !isHydrated,
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

/**
 * Reset auth state for testing
 * @internal
 */
export function resetAuthState() {
  cachedAuthSnapshot = null;
  isSnapshotInitialized = false;
  authListeners = [];
}
