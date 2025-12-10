"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, XCircle, Loader2, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE_URL } from "@/lib/constants";
import { refreshCurrentUser, getAuthToken } from "@/lib/auth";

type VerificationState = "loading" | "success" | "error" | "invalid";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [state, setState] = useState<VerificationState>(token ? "loading" : "invalid");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/verify-email`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token }),
        });

        if (response.ok) {
          setState("success");

          // Refresh user data if logged in
          const token = getAuthToken();
          if (token) {
            try {
              await refreshCurrentUser();
            } catch (error) {
              console.error("Failed to refresh user data:", error);
            }
          }

          // Redirect to login after 3 seconds
          setTimeout(() => {
            router.push("/login?verified=true");
          }, 3000);
        } else {
          const data = await response.json();
          setErrorMessage(data.detail || "Verification failed");
          setState("error");
        }
      } catch (error) {
        console.error("Verification error:", error);
        setErrorMessage("Network error. Please try again.");
        setState("error");
      }
    };

    verifyEmail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="container mx-auto flex min-h-screen items-center justify-center px-4 py-16">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-purple-600">
            {state === "loading" && <Loader2 className="h-8 w-8 animate-spin text-white" />}
            {state === "success" && <CheckCircle2 className="h-8 w-8 text-white" />}
            {state === "error" && <XCircle className="h-8 w-8 text-white" />}
            {state === "invalid" && <Mail className="h-8 w-8 text-white" />}
          </div>

          <CardTitle className="text-2xl">
            {state === "loading" && "Verifying Your Email"}
            {state === "success" && "Email Verified!"}
            {state === "error" && "Verification Failed"}
            {state === "invalid" && "Invalid Link"}
          </CardTitle>

          <CardDescription>
            {state === "loading" && "Please wait while we verify your email address..."}
            {state === "success" && "Your email has been successfully verified."}
            {state === "error" && errorMessage}
            {state === "invalid" && "This verification link is invalid or missing."}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {state === "success" && (
            <div className="rounded-lg bg-green-50 p-4 text-center dark:bg-green-950/30">
              <p className="text-sm text-green-800 dark:text-green-200">
                Redirecting you to login in 3 seconds...
              </p>
            </div>
          )}

          {state === "error" && (
            <div className="space-y-3">
              <div className="rounded-lg bg-red-50 p-4 dark:bg-red-950/30">
                <p className="text-sm text-red-800 dark:text-red-200">Common reasons:</p>
                <ul className="mt-2 list-inside list-disc text-sm text-red-700 dark:text-red-300">
                  <li>Link expired (valid for 24 hours)</li>
                  <li>Already verified</li>
                  <li>Invalid or tampered token</li>
                </ul>
              </div>

              <Button variant="outline" className="w-full" onClick={() => router.push("/login")}>
                Go to Login
              </Button>
            </div>
          )}

          {state === "invalid" && (
            <Button variant="outline" className="w-full" onClick={() => router.push("/")}>
              Go to Home
            </Button>
          )}

          {state === "success" && (
            <Button className="w-full" onClick={() => router.push("/login?verified=true")}>
              Continue to Login
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
