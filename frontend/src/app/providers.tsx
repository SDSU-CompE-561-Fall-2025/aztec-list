"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useState } from "react";
import { ThemeProvider } from "next-themes";
import { QUERY_RETRY_COUNT } from "@/lib/constants";
import { AuthProvider } from "@/contexts/AuthContext";
import { AssistantSheet } from "@/components/ai/AssistantSheet";
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
              // Handle banned users for mutations without their own onError
              // (handleBannedUser dedupes repeat calls itself)
              const message = error instanceof Error ? error.message : String(error);
              if (isBannedError(message)) {
                handleBannedUser();
              }
            },
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
        <AuthProvider>
          {children}
          <AssistantSheet />
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
