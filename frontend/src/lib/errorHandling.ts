import { toast } from "sonner";

/**
 * Check if an error message indicates a banned account.
 */
export function isBannedError(errorMessage: string): boolean {
  return (
    errorMessage.toLowerCase().includes("account banned") ||
    errorMessage.toLowerCase().includes("banned")
  );
}

/**
 * Handle banned user by logging them out and redirecting to login.
 * This should be called when a 403 banned error is detected.
 */
export function handleBannedUser() {
  // Clear auth data
  if (typeof window !== "undefined") {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");

    // Show error message
    toast.error("Your account has been banned. Contact support for assistance.", {
      style: {
        background: "rgb(153, 27, 27)",
        color: "white",
        border: "1px solid rgb(220, 38, 38)",
      },
      duration: 5000,
    });

    // Redirect to login after a short delay
    setTimeout(() => {
      window.location.href = "/login";
    }, 1000);
  }
}

/**
 * Show an error toast. If the user is banned, handle logout and redirect.
 */
export function showErrorToast(
  error: Error | unknown,
  fallbackMessage: string = "An error occurred"
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
