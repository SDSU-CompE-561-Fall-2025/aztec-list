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

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      setIsLoading(true);
      const authToken = await apiLogin(credentials);

      setAuthToken(authToken.access_token);
      setStoredUser(authToken.user);

      notifyAuthListeners();
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (signupData: SignupData): Promise<void> => {
    try {
      await apiSignup(signupData);

      await login({
        username: signupData.email,
        password: signupData.password,
      });
    } catch (error) {
      throw error;
    }
  };

  const logout = (): void => {
    removeAuthToken();
    removeStoredUser();

    notifyAuthListeners();

    router.push("/");
  };

  const updateUser = (updatedUser: User): void => {
    setStoredUser(updatedUser);
    notifyAuthListeners();
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading: isLoading || !isHydrated,
    login,
    signup,
    logout,
    updateUser,
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
