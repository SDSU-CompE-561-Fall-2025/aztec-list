import { toast } from "sonner";
import { endSession, removeAuthToken, removeStoredUser } from "@/lib/auth";

/**
 * Check if an error message indicates a banned account.
 * Checks for the exact error message returned by the backend to avoid false positives.
 */
export function isBannedError(errorMessage: string): boolean {
  return errorMessage.includes("Account banned. Contact support for assistance.");
}

/**
 * Handle banned user by logging them out and redirecting to login.
 * This should be called when a 403 banned error is detected.
 */
export function handleBannedUser() {
  if (typeof window === "undefined") return;

  // The toaster lives in the root layout, so this stays visible across the navigation
  toast.error("Your account has been banned. Contact support for assistance.", {
    style: {
      background: "rgb(153, 27, 27)",
      color: "white",
      border: "1px solid rgb(220, 38, 38)",
    },
    duration: 5000,
  });

  // Clear auth data, then redirect to login after a short delay
  removeAuthToken();
  removeStoredUser();
  setTimeout(() => endSession("/login"), 1000);
}

/**
 * Show an error toast. If the user is banned, handle logout and redirect.
 */
export function showErrorToast(
  error: Error | unknown,
  fallbackMessage: string = "An error occurred",
) {
  const message = error instanceof Error ? error.message : fallbackMessage;

  // If this is a banned error, handle logout and redirect
  if (isBannedError(message)) {
    handleBannedUser();
    return;
  }

  // Otherwise show normal error toast
  toast.error(message, {
    style: {
      background: "rgb(153, 27, 27)",
      color: "white",
      border: "1px solid rgb(220, 38, 38)",
    },
  });
}
