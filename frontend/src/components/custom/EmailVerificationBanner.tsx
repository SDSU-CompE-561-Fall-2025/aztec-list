"use client";

import { useState } from "react";
import { Mail, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { API_BASE_URL } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

export function EmailVerificationBanner() {
  const { user } = useAuth();
  const [isDismissed, setIsDismissed] = useState(false);
  const [isResending, setIsResending] = useState(false);

  if (!user || user.is_verified || isDismissed) {
    return null;
  }

  const handleResend = async () => {
    setIsResending(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: user.email }),
      });

      if (response.ok) {
        toast.success("Verification email sent! Check your inbox.");
      } else {
        const data = await response.json();
        if (response.status === 429) {
          toast.error("Too many requests. Please try again later.");
        } else {
          toast.error(data.detail || "Failed to send verification email");
        }
      }
    } catch (error) {
      console.error("Resend error:", error);
      toast.error("Network error. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="border-b bg-gradient-to-r from-purple-500/10 via-purple-600/10 to-purple-500/10 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-500/20 backdrop-blur-sm">
              <Mail className="h-5 w-5 text-purple-400" />
            </div>
            <div className="flex flex-col gap-0.5">
              <p className="text-sm font-semibold text-foreground">
                Verify your email to create listings
              </p>
              <p className="text-xs text-muted-foreground">
                Check your inbox or{" "}
                <button
                  onClick={handleResend}
                  disabled={isResending}
                  className="inline text-purple-400 hover:text-purple-300 underline underline-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isResending ? "sending..." : "resend verification email"}
                </button>
              </p>
            </div>
          </div>

          <Button
            size="sm"
            variant="ghost"
            onClick={() => setIsDismissed(true)}
            className="text-muted-foreground hover:text-foreground hover:bg-purple-500/10 h-8 w-8 p-0 flex-shrink-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
