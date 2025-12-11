"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Mail, CheckCircle2, Loader2, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE_URL } from "@/lib/constants";

export default function SignupSuccessPage() {
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const [resendError, setResendError] = useState("");
  const [emailSendFailed, setEmailSendFailed] = useState(false);

  useEffect(() => {
    // Check if email sending failed during signup
    const failed = sessionStorage.getItem("email_send_failed");
    if (failed === "true") {
      setEmailSendFailed(true);
      sessionStorage.removeItem("email_send_failed");
    }
  }, []);

  const handleResendEmail = async () => {
    setIsResending(true);
    setResendMessage("");
    setResendError("");

    try {
      const response = await fetch(`${API_BASE_URL}/auth/resend-verification`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        setResendMessage("Verification email sent! Check your inbox.");
      } else {
        const data = await response.json();
        setResendError(data.detail || "Failed to resend email. Please try again later.");
      }
    } catch (error) {
      console.error("Resend error:", error);
      setResendError("Network error. Please try again.");
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="container mx-auto flex min-h-screen items-center justify-center px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-purple-600">
            <CheckCircle2 className="h-8 w-8 text-white" />
          </div>

          <CardTitle className="text-2xl">Account Created!</CardTitle>

          <CardDescription>
            You&apos;re all set! We&apos;ve sent a verification email to your inbox.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {emailSendFailed && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/30">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1 space-y-2">
                  <p className="text-sm font-semibold text-amber-900 dark:text-amber-300">
                    Verification email failed to send
                  </p>
                  <p className="text-sm text-amber-700 dark:text-amber-200/80">
                    Your account was created successfully, but we couldn&apos;t send the
                    verification email. Please use the button below to resend it.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="rounded-lg border border-purple-200 bg-purple-50 p-4 dark:border-purple-800 dark:bg-purple-950/30">
            <div className="flex items-start gap-3">
              <Mail className="h-5 w-5 text-purple-600 dark:text-purple-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <p className="text-sm font-semibold font-medium text-purple-900 dark:text-purple-300">
                  Check your email to unlock listing creation
                </p>
                <p className="text-sm text-purple-700 dark:text-purple-200/80">
                  We&apos;ve sent a verification link to your inbox. Click it to start posting
                  listings. You can browse the marketplace now while you wait!
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-500/30 dark:bg-blue-900/20">
            <div className="flex items-start gap-3">
              <svg
                className="h-5 w-5 flex-shrink-0 text-blue-600 dark:text-blue-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-blue-900 dark:text-blue-300">
                  Didn&apos;t receive the email?
                </p>
                <ul className="list-inside list-disc space-y-0.5 text-sm text-blue-700 dark:text-blue-200/80">
                  <li>Check your spam or junk folder</li>
                  <li>Make sure you used a valid .edu email address</li>
                  <li>Wait a few minutes for the email to arrive</li>
                </ul>
              </div>
            </div>
          </div>

          {resendMessage && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-center dark:border-green-800 dark:bg-green-950/30">
              <p className="text-sm text-green-700 dark:text-green-300">{resendMessage}</p>
            </div>
          )}

          {resendError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-center dark:border-red-800 dark:bg-red-950/30">
              <p className="text-sm text-red-700 dark:text-red-300">{resendError}</p>
            </div>
          )}

          <Button
            variant="outline"
            className="w-full"
            onClick={handleResendEmail}
            disabled={isResending}
          >
            {isResending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Sending...
              </>
            ) : (
              <>
                <Mail className="mr-2 h-4 w-4" />
                Resend Verification Email
              </>
            )}
          </Button>

          <div className="pt-2 text-center">
            <Link href="/">
              <Button className="w-full bg-purple-600 text-white hover:bg-purple-700 dark:bg-purple-600 dark:text-white dark:hover:bg-purple-700">
                Start Browsing Listings
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
