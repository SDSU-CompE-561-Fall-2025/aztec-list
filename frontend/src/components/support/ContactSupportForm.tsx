"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/contexts/AuthContext";
import { API_BASE_URL } from "@/lib/constants";

interface SupportTicketData {
  email: string;
  subject: string;
  message: string;
}

export function ContactSupportForm() {
  const { user } = useAuth();
  const [email, setEmail] = useState(user?.email || "");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<Partial<Record<keyof SupportTicketData, string>>>({});
  const [successMessage, setSuccessMessage] = useState("");

  const createTicketMutation = useMutation({
    mutationFn: async (data: SupportTicketData) => {
      const response = await fetch(`${API_BASE_URL}/support`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to submit ticket");
      }

      return response.json();
    },
    onSuccess: (data) => {
      const message = data.email_sent
        ? "Your ticket has been submitted! Our support team has been notified and will respond to your email within 24-48 hours."
        : "Your ticket has been created. Our team will review it and respond as soon as possible. Note: Email notifications are currently unavailable.";

      setSuccessMessage(message);
      setSubject("");
      setMessage("");
      setErrors({});

      // Clear success message after 8 seconds
      setTimeout(() => setSuccessMessage(""), 8000);
    },
    onError: (error: Error) => {
      setErrors({ message: error.message });
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof SupportTicketData, string>> = {};

    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Invalid email format";
    }

    if (!subject.trim()) {
      newErrors.subject = "Subject is required";
    } else if (subject.length < 3) {
      newErrors.subject = "Subject must be at least 3 characters";
    }

    if (!message.trim()) {
      newErrors.message = "Message is required";
    } else if (message.length < 10) {
      newErrors.message = "Message must be at least 10 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage("");

    if (!validateForm()) return;

    createTicketMutation.mutate({
      email: email.trim(),
      subject: subject.trim(),
      message: message.trim(),
    });
  };

  return (
    <Card className="max-w-2xl mx-auto bg-card border">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500/10 rounded-lg">
            <Mail className="w-6 h-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <CardTitle className="text-2xl text-foreground">Contact Support</CardTitle>
            <CardDescription className="text-muted-foreground mt-1">
              Have a question or need help? Send us a message and we&apos;ll get back to you soon.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {successMessage && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <p className="text-sm text-green-600 dark:text-green-400">{successMessage}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Email */}
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium text-foreground">
              Email <span className="text-red-500">*</span>
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                if (errors.email) setErrors((prev) => ({ ...prev, email: "" }));
              }}
              placeholder="your.email@example.com"
              disabled={!!user?.email}
              className={errors.email ? "border-red-500" : ""}
            />
            {errors.email && <p className="text-sm text-red-500">{errors.email}</p>}
            {user?.email && (
              <p className="text-xs text-muted-foreground">Using your account email address</p>
            )}
          </div>

          {/* Subject */}
          <div className="space-y-2">
            <Label htmlFor="subject" className="text-sm font-medium text-foreground">
              Subject <span className="text-red-500">*</span>
            </Label>
            <Input
              id="subject"
              type="text"
              value={subject}
              onChange={(e) => {
                setSubject(e.target.value);
                if (errors.subject) setErrors((prev) => ({ ...prev, subject: "" }));
              }}
              placeholder="Brief description of your issue"
              className={errors.subject ? "border-red-500" : ""}
            />
            {errors.subject && <p className="text-sm text-red-500">{errors.subject}</p>}
          </div>

          {/* Message */}
          <div className="space-y-2">
            <Label htmlFor="message" className="text-sm font-medium text-foreground">
              Message <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="message"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                if (errors.message) setErrors((prev) => ({ ...prev, message: "" }));
              }}
              placeholder="Please provide as much detail as possible..."
              rows={6}
              className={`resize-none ${errors.message ? "border-red-500" : ""}`}
            />
            {errors.message && <p className="text-sm text-red-500">{errors.message}</p>}
            <p className="text-xs text-muted-foreground">{message.length} / 5000 characters</p>
          </div>

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={createTicketMutation.isPending}
            className="w-full bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-700 hover:to-purple-600 text-white font-semibold"
          >
            {createTicketMutation.isPending ? "Sending..." : "Send Message"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
