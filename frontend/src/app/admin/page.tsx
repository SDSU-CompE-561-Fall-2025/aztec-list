"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { AlertCircle } from "lucide-react";

// Constants - moved outside component for performance
const ACTION_TYPE_CONFIG = {
  strike: {
    label: "Strike",
    bgColor: "bg-yellow-500/10",
    textColor: "text-yellow-400",
    borderColor: "border-yellow-500/20",
  },
  ban: {
    label: "Ban",
    bgColor: "bg-red-500/10",
    textColor: "text-red-400",
    borderColor: "border-red-500/20",
  },
  listing_removal: {
    label: "Listing Removed",
    bgColor: "bg-purple-500/10",
    textColor: "text-purple-400",
    borderColor: "border-purple-500/20",
  },
} as const;

const GUID_REGEX = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;

const TOAST_STYLES = {
  success: {
    background: "rgb(20, 83, 45)",
    color: "white",
    border: "1px solid rgb(34, 197, 94)",
  },
  error: {
    background: "rgb(153, 27, 27)",
    color: "white",
    border: "1px solid rgb(220, 38, 38)",
  },
  warning: {
    background: "rgb(113, 63, 18)",
    color: "white",
    border: "1px solid rgb(251, 191, 36)",
  },
} as const;

// Utility functions - extracted for reusability and testing
const validateGuid = (value: string): string => {
  if (!value.trim()) return "";
  if (!GUID_REGEX.test(value)) {
    return "Invalid UUID format";
  }
  return "";
};

const formatGuid = (value: string): string => {
  const cleaned = value.replace(/[^0-9a-fA-F-]/g, "");
  const hex = cleaned.replace(/-/g, "");
  const limited = hex.slice(0, 32);

  if (limited.length === 0) return "";
  if (limited.length <= 8) return limited;
  if (limited.length <= 12) return `${limited.slice(0, 8)}-${limited.slice(8)}`;
  if (limited.length <= 16)
    return `${limited.slice(0, 8)}-${limited.slice(8, 12)}-${limited.slice(12)}`;
  if (limited.length <= 20)
    return `${limited.slice(0, 8)}-${limited.slice(8, 12)}-${limited.slice(12, 16)}-${limited.slice(16)}`;
  return `${limited.slice(0, 8)}-${limited.slice(8, 12)}-${limited.slice(12, 16)}-${limited.slice(16, 20)}-${limited.slice(20)}`;
};

interface AdminAction {
  id: string;
  admin_id: string;
  admin_username?: string;
  target_user_id: string;
  target_username?: string;
  action_type: string;
  reason: string | null;
  target_listing_id: string | null;
  created_at: string;
  expires_at: string | null;
}

export default function AdminDashboard() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<"actions" | "strike" | "ban" | "remove">("actions");
  const [targetUserId, setTargetUserId] = useState("");
  const [listingId, setListingId] = useState("");
  const [reason, setReason] = useState("");

  // Validation errors
  const [strikeErrors, setStrikeErrors] = useState({ userId: "", reason: "" });
  const [banErrors, setBanErrors] = useState({ userId: "", reason: "" });
  const [removeErrors, setRemoveErrors] = useState({ listingId: "", reason: "" });

  // Fetch admin actions
  const { data: actionsData, isLoading: actionsLoading } = useQuery({
    queryKey: ["adminActions"],
    queryFn: async () => {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}/admin/actions?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to fetch actions");
      return response.json();
    },
    enabled: !!user,
  });

  // Strike mutation
  const strikeMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: string; reason: string }) => {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/strike`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to issue strike" }));
        throw new Error(errorData.detail || "Failed to issue strike");
      }
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["adminActions"] });
      setTargetUserId("");
      setReason("");

      if (data.auto_ban_triggered) {
        toast.error(
          `Strike issued! User has been automatically BANNED after reaching ${data.strike_count} strikes.`,
          {
            duration: 6000,
            style: TOAST_STYLES.error,
          }
        );
      } else {
        toast.success(`Strike issued successfully! User now has ${data.strike_count} strike(s).`, {
          style: TOAST_STYLES.success,
        });
      }
    },
    onError: (error) => {
      // Check if it's an "already banned" error
      if (error.message.includes("already banned")) {
        toast.warning("User is already banned. Cannot issue additional strikes.", {
          style: TOAST_STYLES.warning,
        });
      } else {
        toast.error(`Failed to issue strike: ${error.message}`, {
          style: TOAST_STYLES.error,
        });
      }
    },
  });

  // Ban mutation
  const banMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: string; reason: string }) => {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/ban`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to ban user" }));
        throw new Error(errorData.detail || "Failed to ban user");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminActions"] });
      setTargetUserId("");
      setReason("");
      toast.success("User banned successfully!", {
        style: TOAST_STYLES.success,
      });
    },
    onError: (error) => {
      if (error.message.includes("already banned")) {
        toast.warning("User is already banned. Revoke existing ban first if needed.", {
          style: TOAST_STYLES.warning,
        });
      } else {
        toast.error(`Failed to ban user: ${error.message}`, {
          style: TOAST_STYLES.error,
        });
      }
    },
  });

  // Remove listing mutation
  const removeMutation = useMutation({
    mutationFn: async ({ listingId, reason }: { listingId: string; reason: string }) => {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}/admin/listings/${listingId}/remove`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ reason }),
      });
      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: "Failed to remove listing" }));
        // Check if it's a 404 error
        if (response.status === 404) {
          throw new Error(`Listing not found. The listing ID may be incorrect or already deleted.`);
        }
        throw new Error(errorData.detail || "Failed to remove listing");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminActions"] });
      setListingId("");
      setReason("");
      toast.success("Listing removed successfully!", {
        style: TOAST_STYLES.success,
      });
    },
    onError: (error) => {
      toast.error(`Failed to remove listing: ${error.message}`, {
        style: TOAST_STYLES.error,
      });
    },
  });

  // Revoke action mutation
  const revokeMutation = useMutation({
    mutationFn: async (actionId: string) => {
      const token = getAuthToken();
      const response = await fetch(`${API_BASE_URL}/admin/actions/${actionId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Failed to revoke action");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminActions"] });
      toast.warning("Action revoked successfully!", {
        style: TOAST_STYLES.warning,
      });
    },
    onError: (error) => {
      toast.error(`Failed to revoke action: ${error.message}`, {
        style: TOAST_STYLES.error,
      });
    },
  });

  // Redirect if not admin
  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/");
    }
  }, [authLoading, user, router]);

  if (authLoading) {
    return (
      <div className="container mx-auto p-8 max-w-6xl">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading admin dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!user || user.role !== "admin") {
    return null;
  }

  const actions = actionsData?.items || [];

  return (
    <div className="container mx-auto px-4 py-6 sm:px-6 sm:py-8 max-w-6xl">
      <div className="mb-6 max-w-4xl mx-auto">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Admin Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage users, listings, and moderation actions
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b max-w-4xl mx-auto">
        <button
          onClick={() => setActiveTab("actions")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === "actions"
              ? "border-b-2 border-purple-500 text-purple-300"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Actions History
        </button>
        <button
          onClick={() => setActiveTab("strike")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === "strike"
              ? "border-b-2 border-purple-500 text-purple-400"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          Issue Strike
        </button>
        <button
          onClick={() => setActiveTab("ban")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === "ban"
              ? "border-b-2 border-purple-500 text-purple-400"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          Ban User
        </button>
        <button
          onClick={() => setActiveTab("remove")}
          className={`px-4 py-2 font-medium text-sm transition-colors ${
            activeTab === "remove"
              ? "border-b-2 border-purple-500 text-purple-400"
              : "text-gray-400 hover:text-gray-200"
          }`}
        >
          Remove Listing
        </button>
      </div>

      {/* Actions History Tab */}
      {activeTab === "actions" && (
        <div className="max-w-4xl mx-auto">
          <h2 className="text-lg sm:text-xl font-semibold mb-4 text-white">Recent Admin Actions</h2>
          {actionsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto mb-3"></div>
                <p className="text-muted-foreground text-sm">Loading actions...</p>
              </div>
            </div>
          ) : actions.length === 0 ? (
            <Card className="bg-card border">
              <CardContent className="py-12 text-center">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No actions recorded yet.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-2.5">
              {actions.map((action: AdminAction) => (
                <Card key={action.id} className="bg-card border">
                  <CardContent className="p-3.5">
                    <div className="flex justify-between items-start gap-3">
                      <div className="flex-1 min-w-0 space-y-2">
                        {/* Action Type Badge and Timestamp */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-semibold border ${
                              ACTION_TYPE_CONFIG[
                                action.action_type as keyof typeof ACTION_TYPE_CONFIG
                              ]?.bgColor || "bg-gray-500/10"
                            } ${
                              ACTION_TYPE_CONFIG[
                                action.action_type as keyof typeof ACTION_TYPE_CONFIG
                              ]?.textColor || "text-gray-400"
                            } ${
                              ACTION_TYPE_CONFIG[
                                action.action_type as keyof typeof ACTION_TYPE_CONFIG
                              ]?.borderColor || "border-gray-500/20"
                            }`}
                          >
                            {ACTION_TYPE_CONFIG[
                              action.action_type as keyof typeof ACTION_TYPE_CONFIG
                            ]?.label || action.action_type.replace("_", " ")}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(action.created_at).toLocaleString()}
                          </span>
                        </div>

                        {/* Target User */}
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Target:
                          </span>
                          {action.target_username ? (
                            <span className="text-sm font-medium text-foreground">
                              {action.target_username}
                              <span className="text-xs text-muted-foreground ml-1.5 font-mono">
                                {action.target_user_id}
                              </span>
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground font-mono">
                              {action.target_user_id}
                            </span>
                          )}
                        </div>

                        {/* Admin User */}
                        <div className="flex items-baseline gap-1.5">
                          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                            Admin:
                          </span>
                          {action.admin_username ? (
                            <span className="text-sm text-foreground">
                              {action.admin_username}
                              <span className="text-xs text-muted-foreground ml-1.5 font-mono">
                                {action.admin_id}
                              </span>
                            </span>
                          ) : (
                            <span className="text-xs text-muted-foreground font-mono">
                              {action.admin_id}
                            </span>
                          )}
                        </div>

                        {/* Listing ID if present */}
                        {action.target_listing_id && (
                          <div className="flex items-baseline gap-1.5">
                            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                              Listing:
                            </span>
                            <span className="text-xs text-muted-foreground font-mono">
                              {action.target_listing_id}
                            </span>
                          </div>
                        )}

                        {/* Reason - Most prominent */}
                        {action.reason && (
                          <div className="pt-1.5 mt-1.5 border-t">
                            <p className="text-sm text-foreground leading-relaxed">
                              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide mr-2">
                                Reason:
                              </span>
                              {action.reason}
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Revoke Button */}
                      <Button
                        onClick={() => revokeMutation.mutate(action.id)}
                        disabled={revokeMutation.isPending}
                        variant="destructive"
                        size="sm"
                        className="shrink-0 text-xs"
                      >
                        {revokeMutation.isPending ? "Revoking..." : "Revoke"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Issue Strike Tab */}
      {activeTab === "strike" && (
        <Card className="max-w-xl mx-auto bg-card border">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl text-foreground">
              Issue Strike to User
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Warn a user for policy violations. 3 strikes result in automatic ban.
            </p>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const errors = { userId: "", reason: "" };

                if (!targetUserId.trim()) {
                  errors.userId = "User ID is required";
                }
                if (!reason.trim()) {
                  errors.reason = "Reason is required";
                }

                setStrikeErrors(errors);

                if (errors.userId || errors.reason) {
                  toast.error("Please fill in all required fields", {
                    style: TOAST_STYLES.error,
                  });
                  return;
                }

                strikeMutation.mutate({ userId: targetUserId, reason });
              }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="strike-user-id" className="text-sm font-medium text-foreground">
                  User ID <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="strike-user-id"
                  type="text"
                  value={targetUserId}
                  onChange={(e) => {
                    const formatted = formatGuid(e.target.value);
                    setTargetUserId(formatted);
                    const error = validateGuid(formatted);
                    setStrikeErrors((prev) => ({ ...prev, userId: error }));
                  }}
                  onBlur={(e) => {
                    if (!e.target.value.trim()) {
                      setStrikeErrors((prev) => ({ ...prev, userId: "User ID is required" }));
                    }
                  }}
                  className={`${strikeErrors.userId ? "border-red-500" : ""}`}
                  placeholder="Enter user UUID"
                />
                {strikeErrors.userId && (
                  <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {strikeErrors.userId}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="strike-reason" className="text-sm font-medium text-foreground">
                  Reason <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="strike-reason"
                  value={reason}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                    setReason(e.target.value);
                    if (strikeErrors.reason) setStrikeErrors((prev) => ({ ...prev, reason: "" }));
                  }}
                  onBlur={(e: React.FocusEvent<HTMLTextAreaElement>) => {
                    if (!e.target.value.trim()) {
                      setStrikeErrors((prev) => ({ ...prev, reason: "Reason is required" }));
                    }
                  }}
                  className={`resize-none ${strikeErrors.reason ? "border-red-500" : ""}`}
                  rows={3}
                  placeholder="Reason for strike..."
                />
                {strikeErrors.reason && (
                  <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {strikeErrors.reason}
                  </p>
                )}
              </div>
              <Button
                type="submit"
                disabled={strikeMutation.isPending}
                className="w-full bg-yellow-600 hover:bg-yellow-700 text-white"
              >
                {strikeMutation.isPending ? "Issuing Strike..." : "Issue Strike"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Ban User Tab */}
      {activeTab === "ban" && (
        <Card className="max-w-xl mx-auto bg-card border">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl text-foreground">Ban User</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Permanently ban a user from the platform.
            </p>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const errors = { userId: "", reason: "" };

                if (!targetUserId.trim()) {
                  errors.userId = "User ID is required";
                }
                if (!reason.trim()) {
                  errors.reason = "Reason is required";
                }

                setBanErrors(errors);

                if (errors.userId || errors.reason) {
                  toast.error("Please fill in all required fields", {
                    style: TOAST_STYLES.error,
                  });
                  return;
                }

                banMutation.mutate({ userId: targetUserId, reason });
              }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="ban-user-id" className="text-sm font-medium text-foreground">
                  User ID <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="ban-user-id"
                  type="text"
                  value={targetUserId}
                  onChange={(e) => {
                    const formatted = formatGuid(e.target.value);
                    setTargetUserId(formatted);
                    const error = validateGuid(formatted);
                    setBanErrors((prev) => ({ ...prev, userId: error }));
                  }}
                  onBlur={(e) => {
                    if (!e.target.value.trim()) {
                      setBanErrors((prev) => ({ ...prev, userId: "User ID is required" }));
                    }
                  }}
                  className={`${banErrors.userId ? "border-red-500" : ""}`}
                  placeholder="Enter user UUID"
                />
                {banErrors.userId && (
                  <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {banErrors.userId}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ban-reason" className="text-sm font-medium text-foreground">
                  Reason <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="ban-reason"
                  value={reason}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                    setReason(e.target.value);
                    if (banErrors.reason) setBanErrors((prev) => ({ ...prev, reason: "" }));
                  }}
                  onBlur={(e: React.FocusEvent<HTMLTextAreaElement>) => {
                    if (!e.target.value.trim()) {
                      setBanErrors((prev) => ({ ...prev, reason: "Reason is required" }));
                    }
                  }}
                  className={`resize-none ${banErrors.reason ? "border-red-500" : ""}`}
                  rows={3}
                  placeholder="Reason for ban..."
                />
                {banErrors.reason && (
                  <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {banErrors.reason}
                  </p>
                )}
              </div>
              <Button
                type="submit"
                disabled={banMutation.isPending}
                variant="destructive"
                className="w-full"
              >
                {banMutation.isPending ? "Banning User..." : "Ban User (Permanent)"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Remove Listing Tab */}
      {activeTab === "remove" && (
        <Card className="max-w-xl mx-auto bg-card border">
          <CardHeader>
            <CardTitle className="text-lg sm:text-xl text-foreground">Remove Listing</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Delete a listing and issue a strike to its owner.
            </p>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const errors = { listingId: "", reason: "" };

                if (!listingId.trim()) {
                  errors.listingId = "Listing ID is required";
                }
                if (!reason.trim()) {
                  errors.reason = "Reason is required";
                }

                setRemoveErrors(errors);

                if (errors.listingId || errors.reason) {
                  toast.error("Please fill in all required fields", {
                    style: TOAST_STYLES.error,
                  });
                  return;
                }

                removeMutation.mutate({ listingId, reason });
              }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="remove-listing-id" className="text-sm font-medium text-foreground">
                  Listing ID <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="remove-listing-id"
                  type="text"
                  value={listingId}
                  onChange={(e) => {
                    const formatted = formatGuid(e.target.value);
                    setListingId(formatted);
                    const error = validateGuid(formatted);
                    setRemoveErrors((prev) => ({ ...prev, listingId: error }));
                  }}
                  onBlur={(e) => {
                    if (!e.target.value.trim()) {
                      setRemoveErrors((prev) => ({ ...prev, listingId: "Listing ID is required" }));
                    }
                  }}
                  className={`${removeErrors.listingId ? "border-red-500" : ""}`}
                  placeholder="Enter listing UUID"
                />
                {removeErrors.listingId && (
                  <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {removeErrors.listingId}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="remove-reason" className="text-sm font-medium text-foreground">
                  Reason <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="remove-reason"
                  value={reason}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                    setReason(e.target.value);
                    if (removeErrors.reason) setRemoveErrors((prev) => ({ ...prev, reason: "" }));
                  }}
                  onBlur={(e: React.FocusEvent<HTMLTextAreaElement>) => {
                    if (!e.target.value.trim()) {
                      setRemoveErrors((prev) => ({ ...prev, reason: "Reason is required" }));
                    }
                  }}
                  className={`resize-none ${removeErrors.reason ? "border-red-500" : ""}`}
                  rows={3}
                  placeholder="Reason for removal..."
                />
                {removeErrors.reason && (
                  <p className="text-red-400 text-xs mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {removeErrors.reason}
                  </p>
                )}
              </div>
              <Button
                type="submit"
                disabled={removeMutation.isPending}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              >
                {removeMutation.isPending ? "Removing Listing..." : "Remove Listing"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
