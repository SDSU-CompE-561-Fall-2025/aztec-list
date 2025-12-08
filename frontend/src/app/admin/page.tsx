"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import { toast } from "sonner";

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

  // Validate GUID format
  const validateGuid = (value: string): string => {
    if (!value.trim()) return "";
    const guidRegex = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;
    if (!guidRegex.test(value)) {
      return "Invalid UUID format";
    }
    return "";
  };

  // Format GUID (add hyphens if needed)
  const formatGuid = (value: string): string => {
    // Remove all non-hex characters except hyphens
    const cleaned = value.replace(/[^0-9a-fA-F-]/g, "");
    // Remove existing hyphens to reformat
    const hex = cleaned.replace(/-/g, "");
    // Limit to 32 hex characters
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
      // Validate GUID format
      const guidRegex = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;
      if (!guidRegex.test(userId)) {
        throw new Error("Invalid user ID format. Please enter a valid UUID.");
      }

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
          { duration: 6000 }
        );
      } else {
        toast.success(`Strike issued successfully! User now has ${data.strike_count} strike(s).`);
      }
    },
    onError: (error) => {
      // Check if it's an "already banned" error
      if (error.message.includes("already banned")) {
        toast.warning("User is already banned. Cannot issue additional strikes.");
      } else {
        toast.error(`Failed to issue strike: ${error.message}`);
      }
    },
  });

  // Ban mutation
  const banMutation = useMutation({
    mutationFn: async ({ userId, reason }: { userId: string; reason: string }) => {
      // Validate GUID format
      const guidRegex = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;
      if (!guidRegex.test(userId)) {
        throw new Error("Invalid user ID format. Please enter a valid UUID.");
      }

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
      toast.success("User banned successfully!");
    },
    onError: (error) => {
      // Check if it's an "already banned" error
      if (error.message.includes("already banned")) {
        toast.warning("User is already banned. Revoke existing ban first if needed.");
      } else {
        toast.error(`Failed to ban user: ${error.message}`);
      }
    },
  });

  // Remove listing mutation
  const removeMutation = useMutation({
    mutationFn: async ({ listingId, reason }: { listingId: string; reason: string }) => {
      // Validate GUID format
      const guidRegex = /^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$/i;
      if (!guidRegex.test(listingId)) {
        throw new Error("Invalid listing ID format. Please enter a valid UUID.");
      }

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
      toast.success("Listing removed successfully!");
    },
    onError: (error) => {
      toast.error(`Failed to remove listing: ${error.message}`);
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
      toast.warning("Action revoked successfully!");
    },
    onError: (error) => {
      toast.error(`Failed to revoke action: ${error.message}`);
    },
  });

  // Redirect if not admin
  useEffect(() => {
    if (!authLoading && (!user || user.role !== "admin")) {
      router.push("/");
    }
  }, [authLoading, user, router]);

  if (authLoading) {
    return <div className="p-8">Loading...</div>;
  }

  if (!user || user.role !== "admin") {
    return null;
  }

  const actions = actionsData?.items || [];

  return (
    <div className="container mx-auto p-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <button
          onClick={() => setActiveTab("actions")}
          className={`px-4 py-2 font-medium ${
            activeTab === "actions"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-600 hover:text-gray-800"
          }`}
        >
          Actions History
        </button>
        <button
          onClick={() => setActiveTab("strike")}
          className={`px-4 py-2 font-medium ${
            activeTab === "strike"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-600 hover:text-gray-800"
          }`}
        >
          Issue Strike
        </button>
        <button
          onClick={() => setActiveTab("ban")}
          className={`px-4 py-2 font-medium ${
            activeTab === "ban"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-600 hover:text-gray-800"
          }`}
        >
          Ban User
        </button>
        <button
          onClick={() => setActiveTab("remove")}
          className={`px-4 py-2 font-medium ${
            activeTab === "remove"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-600 hover:text-gray-800"
          }`}
        >
          Remove Listing
        </button>
      </div>

      {/* Actions History Tab */}
      {activeTab === "actions" && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Recent Admin Actions</h2>
          {actionsLoading ? (
            <p>Loading actions...</p>
          ) : actions.length === 0 ? (
            <p className="text-gray-500">No actions recorded yet.</p>
          ) : (
            <div className="space-y-4">
              {actions.map((action: AdminAction) => (
                <div
                  key={action.id}
                  className="border border-gray-700 rounded-lg p-4 bg-gray-800 shadow-sm"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-semibold text-lg capitalize text-gray-100">
                          {action.action_type.replace("_", " ")}
                        </span>
                        <span className="text-sm text-gray-400">
                          {new Date(action.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-300">
                        <strong>Target User:</strong>{" "}
                        {action.target_username ? (
                          <>
                            {action.target_username}{" "}
                            <span className="text-gray-500">({action.target_user_id})</span>
                          </>
                        ) : (
                          action.target_user_id
                        )}
                      </p>
                      <p className="text-sm text-gray-300">
                        <strong>Admin:</strong>{" "}
                        {action.admin_username ? (
                          <>
                            {action.admin_username}{" "}
                            <span className="text-gray-500">({action.admin_id})</span>
                          </>
                        ) : (
                          action.admin_id
                        )}
                      </p>
                      {action.target_listing_id && (
                        <p className="text-sm text-gray-300">
                          <strong>Listing:</strong> {action.target_listing_id}
                        </p>
                      )}
                      {action.reason && (
                        <p className="text-sm text-gray-200 mt-2">
                          <strong>Reason:</strong> {action.reason}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => revokeMutation.mutate(action.id)}
                      disabled={revokeMutation.isPending}
                      className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Issue Strike Tab */}
      {activeTab === "strike" && (
        <div className="max-w-md">
          <h2 className="text-xl font-semibold mb-4">Issue Strike to User</h2>
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
                toast.error("Please fill in all required fields");
                return;
              }

              strikeMutation.mutate({ userId: targetUserId, reason });
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium mb-1">
                User ID <span className="text-red-500">*</span>
              </label>
              <input
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
                className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  strikeErrors.userId ? "border-red-500" : "border-gray-700"
                }`}
                placeholder="Enter user UUID"
              />
              {strikeErrors.userId && (
                <p className="text-red-500 text-sm mt-1">{strikeErrors.userId}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  if (strikeErrors.reason) setStrikeErrors((prev) => ({ ...prev, reason: "" }));
                }}
                onBlur={(e) => {
                  if (!e.target.value.trim()) {
                    setStrikeErrors((prev) => ({ ...prev, reason: "Reason is required" }));
                  }
                }}
                className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                  strikeErrors.reason ? "border-red-500" : "border-gray-700"
                }`}
                rows={3}
                placeholder="Reason for strike..."
              />
              {strikeErrors.reason && (
                <p className="text-red-500 text-sm mt-1">{strikeErrors.reason}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={strikeMutation.isPending}
              className="w-full px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
            >
              {strikeMutation.isPending ? "Issuing Strike..." : "Issue Strike"}
            </button>
          </form>
        </div>
      )}

      {/* Ban User Tab */}
      {activeTab === "ban" && (
        <div className="max-w-md">
          <h2 className="text-xl font-semibold mb-4">Ban User</h2>
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
                toast.error("Please fill in all required fields");
                return;
              }

              banMutation.mutate({ userId: targetUserId, reason });
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium mb-1">
                User ID <span className="text-red-500">*</span>
              </label>
              <input
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
                className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  banErrors.userId ? "border-red-500" : "border-gray-700"
                }`}
                placeholder="Enter user UUID"
              />
              {banErrors.userId && <p className="text-red-500 text-sm mt-1">{banErrors.userId}</p>}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  if (banErrors.reason) setBanErrors((prev) => ({ ...prev, reason: "" }));
                }}
                onBlur={(e) => {
                  if (!e.target.value.trim()) {
                    setBanErrors((prev) => ({ ...prev, reason: "Reason is required" }));
                  }
                }}
                className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                  banErrors.reason ? "border-red-500" : "border-gray-700"
                }`}
                rows={3}
                placeholder="Reason for ban..."
              />
              {banErrors.reason && <p className="text-red-500 text-sm mt-1">{banErrors.reason}</p>}
            </div>
            <button
              type="submit"
              disabled={banMutation.isPending}
              className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              {banMutation.isPending ? "Banning User..." : "Ban User (Permanent)"}
            </button>
          </form>
        </div>
      )}

      {/* Remove Listing Tab */}
      {activeTab === "remove" && (
        <div className="max-w-md">
          <h2 className="text-xl font-semibold mb-4">Remove Listing</h2>
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
                toast.error("Please fill in all required fields");
                return;
              }

              removeMutation.mutate({ listingId, reason });
            }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium mb-1">
                Listing ID <span className="text-red-500">*</span>
              </label>
              <input
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
                className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  removeErrors.listingId ? "border-red-500" : "border-gray-700"
                }`}
                placeholder="Enter listing UUID"
              />
              {removeErrors.listingId && (
                <p className="text-red-500 text-sm mt-1">{removeErrors.listingId}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  if (removeErrors.reason) setRemoveErrors((prev) => ({ ...prev, reason: "" }));
                }}
                onBlur={(e) => {
                  if (!e.target.value.trim()) {
                    setRemoveErrors((prev) => ({ ...prev, reason: "Reason is required" }));
                  }
                }}
                className={`w-full px-3 py-2 bg-gray-900 border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${
                  removeErrors.reason ? "border-red-500" : "border-gray-700"
                }`}
                rows={3}
                placeholder="Reason for removal..."
              />
              {removeErrors.reason && (
                <p className="text-red-500 text-sm mt-1">{removeErrors.reason}</p>
              )}
            </div>
            <button
              type="submit"
              disabled={removeMutation.isPending}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
            >
              {removeMutation.isPending ? "Removing Listing..." : "Remove Listing"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
