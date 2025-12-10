"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState } from "react";
import { ThemeProvider } from "next-themes";
import { QUERY_RETRY_COUNT } from "@/lib/constants";
import { AuthProvider } from "@/contexts/AuthContext";
import { isBannedError, handleBannedUser } from "@/lib/errorHandling";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: QUERY_RETRY_COUNT,
            refetchOnWindowFocus: false,
          },
          mutations: {
            onError: (error) => {
              // Automatically handle banned users globally
              const message = error instanceof Error ? error.message : String(error);
              if (isBannedError(message)) {
                // Track if we've already handled this to prevent duplicate logout/redirects
                if (
                  typeof window !== "undefined" &&
                  !window.sessionStorage.getItem("banned_handler_called")
                ) {
                  window.sessionStorage.setItem("banned_handler_called", "true");
                  handleBannedUser();
                }
              }
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
