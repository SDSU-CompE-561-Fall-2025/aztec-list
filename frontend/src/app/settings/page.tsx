"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import { toast } from "sonner";
import {
  ChevronLeft,
  Trash2,
  AlertTriangle,
  Upload,
  Mail,
  CheckCircle2,
  Loader2,
} from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/custom/ProtectedRoute";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken, setStoredUser, changePassword, refreshCurrentUser } from "@/lib/auth";
import { updateProfile, updateProfilePicture, removeProfilePicture, getMyProfile } from "@/lib/api";
import { showErrorToast } from "@/lib/errorHandling";
import { createProfileQueryOptions } from "@/queryOptions/createProfileQueryOptions";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import type { ContactInfo } from "@/types/user";

/**
 * Calculate password strength score (0-4).
 */
function getPasswordStrength(password: string): number {
  let strength = 0;
  if (password.length >= 8) strength++;
  if (password.length >= 12) strength++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
  if (/\d/.test(password)) strength++;
  if (/[^a-zA-Z0-9]/.test(password)) strength++;
  return Math.min(strength, 4);
}

/**
 * Get password strength label and color.
 */
function getPasswordStrengthInfo(strength: number): { label: string; color: string } {
  const levels = [
    { label: "Too weak", color: "bg-red-500" },
    { label: "Weak", color: "bg-orange-500" },
    { label: "Fair", color: "bg-yellow-500" },
    { label: "Good", color: "bg-blue-500" },
    { label: "Strong", color: "bg-green-500" },
  ];
  return levels[strength] || levels[0];
}

interface ProfileUpdatePayload {
  name?: string | null;
  campus?: string | null;
  contact_info?: ContactInfo;
}

function SettingsContent() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const queryClient = useQueryClient();

  // Profile form state
  const [formName, setFormName] = useState("");
  const [formCampus, setFormCampus] = useState("");
  const [formPhone, setFormPhone] = useState("");
  const [phoneError, setPhoneError] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [stagedPictureFile, setStagedPictureFile] = useState<File | null>(null);
  const [isPictureRemovalStaged, setIsPictureRemovalStaged] = useState(false);
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const isInitializedRef = useRef(false);
  const hasRefreshedRef = useRef(false);

  // Fetch existing profile data using React Query
  const { data: profile, isLoading: isProfileFetching } = useQuery(
    createProfileQueryOptions(user?.id),
  );

  // Initialize form state from fetched profile (only once)
  useEffect(() => {
    if (!isProfileFetching && profile && !isInitializedRef.current) {
      isInitializedRef.current = true;
      setIsInitialLoading(false);
      setFormName(profile.name || "");
      setFormCampus(profile.campus || "");
      setFormPhone(profile.contact_info?.phone || "");
    } else if (!isProfileFetching && !profile) {
      setIsInitialLoading(false);
    }
  }, [profile, isProfileFetching]);

  // Track if profile has changes (memoized to avoid unnecessary recalculations)
  const hasProfileChanges = useMemo(
    () =>
      formName !== (profile?.name || "") ||
      formCampus !== (profile?.campus || "") ||
      formPhone !== (profile?.contact_info?.phone || "") ||
      stagedPictureFile !== null ||
      isPictureRemovalStaged,
    [formName, formCampus, formPhone, profile, stagedPictureFile, isPictureRemovalStaged],
  );

  // Check if form is valid for submission
  const isFormValid = useMemo(() => !phoneError, [phoneError]);

  // Account state
  const [username, setUsername] = useState(user?.username ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [isAccountLoading, setIsAccountLoading] = useState(false);

  // Track if account has changes (memoized)
  const hasAccountChanges = useMemo(
    () => username !== (user?.username ?? "") || email !== (user?.email ?? ""),
    [username, email, user?.username, user?.email],
  );

  // Delete account state
  const [isDeleting, setIsDeleting] = useState(false);

  // Email verification state
  const [isResendingVerification, setIsResendingVerification] = useState(false);

  // Cancel confirmation dialogs
  const [showProfileCancelDialog, setShowProfileCancelDialog] = useState(false);
  const [showAccountCancelDialog, setShowAccountCancelDialog] = useState(false);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);
  const hasInitializedUsernameRef = useRef(false);

  // Calculate password strength
  const passwordStrength = getPasswordStrength(newPassword);
  const strengthInfo = getPasswordStrengthInfo(passwordStrength);

  // Initialize username and email from user data (only once)
  useEffect(() => {
    if (user?.username && !hasInitializedUsernameRef.current) {
      hasInitializedUsernameRef.current = true;
      setUsername(user.username);
      setEmail(user.email);
    }
  }, [user]);

  // Refresh user data on mount to ensure we have latest verification status
  useEffect(() => {
    if (!user || hasRefreshedRef.current) return;

    hasRefreshedRef.current = true;

    const refreshUser = async () => {
      try {
        await refreshCurrentUser();
      } catch (error) {
        console.error("Failed to refresh user data:", error);
      }
    };

    refreshUser();
  }, [user]);

  // Format and validate phone number
  const formatPhoneNumber = (value: string): string => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, "");

    // Limit to 10 digits
    const limited = digits.slice(0, 10);

    // Format as (XXX) XXX-XXXX
    if (limited.length === 0) return "";
    if (limited.length <= 3) return `(${limited}`;
    if (limited.length <= 6) return `(${limited.slice(0, 3)}) ${limited.slice(3)}`;
    return `(${limited.slice(0, 3)}) ${limited.slice(3, 6)}-${limited.slice(6)}`;
  };

  const validatePhoneNumber = (value: string): boolean => {
    if (value === "") {
      setPhoneError("");
      return true;
    }
    const digits = value.replace(/\D/g, "");
    if (digits.length !== 10) {
      setPhoneError("Phone number must be 10 digits");
      return false;
    }
    setPhoneError("");
    return true;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhoneNumber(e.target.value);
    setFormPhone(formatted);
    validatePhoneNumber(formatted);
  };

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate phone before submitting
    if (!validatePhoneNumber(formPhone)) {
      toast.error("Please enter a valid phone number or leave it empty", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      return;
    }

    setIsProfileLoading(true);

    try {
      // Step 1: Handle profile picture upload if staged
      if (stagedPictureFile) {
        await updateProfilePicture(stagedPictureFile);
      }

      // Step 2: Handle profile picture removal if staged
      if (isPictureRemovalStaged) {
        await removeProfilePicture();
      }

      // Step 3: Update other profile fields
      const updates: ProfileUpdatePayload = {};

      if (formName !== (profile?.name || "")) {
        updates.name = formName.trim() || null; // null clears the field
      }

      if (formCampus !== (profile?.campus || "")) {
        updates.campus = formCampus.trim() || null; // null clears the field
      }

      const originalPhone = profile?.contact_info?.phone || "";
      if (formPhone !== originalPhone) {
        if (!user?.email) {
          throw new Error("User email not available");
        }
        updates.contact_info = {
          email: user.email,
          phone: formPhone.trim() || undefined,
        };
      }

      // Update profile fields if there are changes
      if (Object.keys(updates).length > 0) {
        await updateProfile(updates);
      }

      // Fetch updated profile to get latest data with fresh updated_at timestamp
      // This is done regardless of whether fields were updated, since picture changes also need refresh
      const updatedProfile = await getMyProfile();

      // Update the React Query cache with fresh data from server
      // This triggers all components using this query to re-render with new updated_at
      queryClient.setQueryData(["profile", user?.id], updatedProfile);

      // Update form fields to match the saved data
      setFormName(updatedProfile.name || "");
      setFormCampus(updatedProfile.campus || "");
      setFormPhone(updatedProfile.contact_info?.phone || "");

      // Clear staged changes
      setPreviewUrl(null);
      setStagedPictureFile(null);
      setIsPictureRemovalStaged(false);

      toast.success("Profile saved successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
    } catch (error) {
      showErrorToast(error, "Failed to save profile");
    } finally {
      setIsProfileLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      e.target.value = ""; // Reset input
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image must be smaller than 5MB", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      e.target.value = ""; // Reset input
      return;
    }

    // Stage the file for upload (don't upload yet)
    setStagedPictureFile(file);
    setIsPictureRemovalStaged(false);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Reset input to allow uploading same file again
    e.target.value = "";
  };

  const handleStagePictureRemoval = () => {
    // Stage removal (don't remove yet, wait for Save)
    setIsPictureRemovalStaged(true);
    setStagedPictureFile(null);
    setPreviewUrl(null);
  };

  const handleCancelProfileChanges = () => {
    // Reset all profile fields to original values
    setFormName(profile?.name || "");
    setFormCampus(profile?.campus || "");
    setFormPhone(profile?.contact_info?.phone || "");
    setStagedPictureFile(null);
    setIsPictureRemovalStaged(false);
    setPreviewUrl(null);
    setPhoneError("");
    setShowProfileCancelDialog(false);
  };

  const handleAccountUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAccountLoading(true);

    try {
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");

      if (username === user?.username && email === user?.email) {
        toast.info("No changes to save");
        setIsAccountLoading(false);
        return;
      }

      // Validate .edu email requirement
      if (email !== user?.email && !email.toLowerCase().endsWith(".edu")) {
        toast.error("Email must be from a .edu domain", {
          style: {
            background: "rgb(153, 27, 27)",
            color: "white",
            border: "1px solid rgb(220, 38, 38)",
          },
        });
        setIsAccountLoading(false);
        return;
      }

      const updateData: { username?: string; email?: string } = {};
      if (username !== user?.username) updateData.username = username;
      if (email !== user?.email) updateData.email = email;

      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update account");
      }

      // Get updated user data from response
      const updatedUser = await response.json();

      // Check if email sending failed
      if (updatedUser.verification_email_sent === false) {
        toast.warning(
          "Account updated but verification email failed to send. Please try resending it from the settings page.",
          {
            style: {
              background: "rgb(113, 63, 18)",
              color: "white",
              border: "1px solid rgb(251, 146, 60)",
            },
            duration: 8000,
          },
        );
      }

      // Update localStorage - this will automatically sync AuthContext via custom event
      setStoredUser(updatedUser);

      // Invalidate all queries that might display the username
      queryClient.invalidateQueries({ queryKey: ["user"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });

      // Show different message if email was changed
      if (email !== user?.email) {
        if (updatedUser.verification_email_sent !== false) {
          toast.success(
            "Email updated! Please check your inbox to verify your new email address.",
            {
              style: {
                background: "rgb(20, 83, 45)",
                color: "white",
                border: "1px solid rgb(34, 197, 94)",
              },
              duration: 6000,
            },
          );
        }
      } else {
        toast.success("Account updated successfully!", {
          style: {
            background: "rgb(20, 83, 45)",
            color: "white",
            border: "1px solid rgb(34, 197, 94)",
          },
        });
      }
    } catch (error) {
      // Reset username and email to original values on error
      setUsername(user?.username ?? "");
      setEmail(user?.email ?? "");
      showErrorToast(error, "Failed to update account");
    } finally {
      setIsAccountLoading(false);
    }
  };

  const handleCancelAccountChanges = () => {
    // Reset username and email to original values
    setUsername(user?.username ?? "");
    setEmail(user?.email ?? "");
    setShowAccountCancelDialog(false);
  };

  const handleResendVerification = async () => {
    if (!user?.email) return;

    setIsResendingVerification(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/resend-verification?email=${encodeURIComponent(user.email)}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (response.ok) {
        toast.success("Verification email sent! Check your inbox.", {
          style: {
            background: "rgb(20, 83, 45)",
            color: "white",
            border: "1px solid rgb(34, 197, 94)",
          },
        });
      } else {
        const data = await response.json();
        if (response.status === 429) {
          toast.error("Too many requests. Please try again later.");
        } else {
          // Handle validation errors (array) or string errors
          let errorMsg = "Failed to send verification email";
          if (typeof data.detail === "string") {
            errorMsg = data.detail;
          } else if (Array.isArray(data.detail)) {
            // FastAPI validation errors
            errorMsg = data.detail.map((err: { msg: string }) => err.msg).join(", ");
          }
          toast.error(errorMsg);
        }
      }
    } catch (error) {
      showErrorToast(error, "Failed to resend verification email");
    } finally {
      setIsResendingVerification(false);
    }
  };

  const handleDeleteAccount = async () => {
    setIsDeleting(true);

    try {
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");

      // Delete account on backend first
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to delete account");
      }

      // Log out and redirect to home
      logout();
      toast.success("Account deleted successfully", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
      router.push("/");
    } catch (error) {
      showErrorToast(error, "Failed to delete account");
      setIsDeleting(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("All password fields are required", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      return;
    }

    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      return;
    }

    if (newPassword === currentPassword) {
      toast.error("New password must be different from current password", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match", {
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
      return;
    }

    setIsPasswordLoading(true);

    try {
      await changePassword(currentPassword, newPassword);

      toast.success("Password changed successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });

      // Clear form
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      showErrorToast(error, "Failed to change password");
    } finally {
      setIsPasswordLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background px-4 py-4 sm:px-6 sm:py-6 lg:px-8">
      <div className="mx-auto w-full max-w-2xl">
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          <Button
            variant="ghost"
            className="mb-3 -ml-3 text-muted-foreground hover:text-foreground"
            onClick={() => router.push("/profile")}
          >
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Profile
          </Button>
          <h1 className="mb-1 text-2xl font-bold text-foreground sm:text-3xl">Account Settings</h1>
          <p className="text-sm text-muted-foreground sm:text-base">
            Manage your account preferences and information
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="profile" className="space-y-3 sm:space-y-4">
          <TabsList className="grid h-auto w-full grid-cols-3 border bg-muted p-1">
            <TabsTrigger
              value="profile"
              className="text-xs data-[state=active]:bg-background sm:text-sm"
            >
              Profile
            </TabsTrigger>
            <TabsTrigger
              value="account"
              className="text-xs data-[state=active]:bg-background sm:text-sm"
            >
              Account
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="text-xs data-[state=active]:bg-background sm:text-sm"
            >
              Security
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card className="border bg-card">
              <CardHeader>
                <CardTitle className="text-lg text-foreground sm:text-xl">
                  Profile Information
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground sm:text-sm">
                  Add details to help buyers connect with you
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isInitialLoading ? (
                  <div className="space-y-6">
                    {/* Profile Picture Skeleton */}
                    <div className="border-b pb-6">
                      <div className="flex items-center gap-4">
                        <div className="h-16 w-16 animate-pulse rounded-full bg-muted"></div>
                        <div className="flex gap-2">
                          <div className="h-9 w-[72px] animate-pulse rounded bg-muted"></div>
                          <div className="h-9 w-[76px] animate-pulse rounded bg-muted"></div>
                        </div>
                      </div>
                    </div>
                    {/* Form Fields Skeleton */}
                    <div className="space-y-3">
                      <div className="space-y-1.5">
                        <div className="h-5 w-[70px] animate-pulse rounded bg-muted"></div>
                        <div className="h-9 animate-pulse rounded bg-muted"></div>
                      </div>
                      <div className="space-y-1.5">
                        <div className="h-5 w-[52px] animate-pulse rounded bg-muted"></div>
                        <div className="h-9 animate-pulse rounded bg-muted"></div>
                      </div>
                      <div className="space-y-1.5">
                        <div className="h-5 w-[104px] animate-pulse rounded bg-muted"></div>
                        <div className="h-9 animate-pulse rounded bg-muted"></div>
                        <div className="mt-1.5 h-4 w-[172px] animate-pulse rounded bg-muted"></div>
                      </div>
                      <div className="pt-2">
                        <div className="h-9 animate-pulse rounded bg-muted"></div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Profile Picture Section */}
                    <div className="mb-6 border-b pb-6">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="group relative flex h-16 w-16 items-center justify-center overflow-hidden rounded-full border-2 border-purple-500/30 bg-gradient-to-br from-purple-500/20 to-purple-600/20">
                            {isPictureRemovalStaged ? (
                              <span className="text-xl font-bold text-purple-300">
                                {user?.username?.substring(0, 2).toUpperCase() || "??"}
                              </span>
                            ) : previewUrl ? (
                              <Image
                                src={previewUrl}
                                alt="Profile Preview"
                                fill
                                sizes="64px"
                                className="object-cover"
                              />
                            ) : !isProfileFetching && profile?.profile_picture_url ? (
                              <Image
                                src={
                                  getProfilePictureUrl(
                                    profile.profile_picture_url,
                                    profile.updated_at,
                                  ) || ""
                                }
                                alt="Profile"
                                fill
                                sizes="64px"
                                className="object-cover"
                              />
                            ) : (
                              <span className="text-xl font-bold text-purple-300">
                                {user?.username?.substring(0, 2).toUpperCase() || "??"}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <input
                            id="profilePictureFile"
                            type="file"
                            accept="image/*"
                            onChange={handleFileSelect}
                            disabled={isProfileLoading}
                            className="hidden"
                          />
                          <label htmlFor="profilePictureFile">
                            <Button
                              type="button"
                              asChild
                              disabled={isProfileLoading}
                              size="sm"
                              className="cursor-pointer bg-purple-600 text-white hover:bg-purple-700"
                            >
                              <span>
                                <Upload className="mr-2 h-4 w-4" />
                                {stagedPictureFile ? "Change" : "Upload"}
                              </span>
                            </Button>
                          </label>
                          {(profile?.profile_picture_url || previewUrl) &&
                            !isPictureRemovalStaged && (
                              <Button
                                type="button"
                                onClick={handleStagePictureRemoval}
                                disabled={isProfileLoading}
                                size="sm"
                                variant="outline"
                                className="border-red-900/50 text-red-400 hover:bg-red-900/20 hover:text-red-300"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Remove
                              </Button>
                            )}
                        </div>
                      </div>
                    </div>

                    <form onSubmit={handleProfileSave} className="space-y-3">
                      <div className="space-y-1.5">
                        <Label htmlFor="name" className="text-sm text-foreground sm:text-base">
                          Full Name
                        </Label>
                        <Input
                          id="name"
                          type="text"
                          placeholder="John Doe"
                          value={formName}
                          onChange={(e) => setFormName(e.target.value)}
                          disabled={isProfileLoading}
                          className="text-sm placeholder:text-muted-foreground/50"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <Label htmlFor="campus" className="text-sm text-foreground sm:text-base">
                          Campus
                        </Label>
                        <Input
                          id="campus"
                          type="text"
                          placeholder="San Diego State University"
                          value={formCampus}
                          onChange={(e) => setFormCampus(e.target.value)}
                          disabled={isProfileLoading}
                          className="text-sm placeholder:text-muted-foreground/50"
                        />
                      </div>

                      <div className="space-y-1.5">
                        <Label htmlFor="phone" className="text-sm text-foreground sm:text-base">
                          Phone Number
                        </Label>
                        <Input
                          id="phone"
                          type="tel"
                          placeholder="(555) 123-4567"
                          value={formPhone}
                          onChange={handlePhoneChange}
                          disabled={isProfileLoading}
                          className={`text-sm placeholder:text-muted-foreground/50 ${phoneError ? "border-red-500" : ""}`}
                        />
                        {phoneError ? (
                          <p className="text-xs text-red-500">{phoneError}</p>
                        ) : (
                          <p className="text-xs text-muted-foreground sm:text-sm">
                            US format: (555) 123-4567
                          </p>
                        )}
                      </div>

                      <div className="flex gap-3 pt-2">
                        <Button
                          type="submit"
                          className="flex-1 bg-purple-600 text-sm text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50 sm:text-base"
                          disabled={isProfileLoading || !hasProfileChanges || !isFormValid}
                        >
                          {isProfileLoading ? "Saving..." : "Save Profile"}
                        </Button>
                        {hasProfileChanges && (
                          <Button
                            type="button"
                            onClick={() => setShowProfileCancelDialog(true)}
                            disabled={isProfileLoading}
                            variant="outline"
                            className="flex-1 border-red-900/50 text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300 sm:text-base"
                          >
                            Cancel
                          </Button>
                        )}
                      </div>
                    </form>

                    {/* Profile Cancel Dialog */}
                    <AlertDialog
                      open={showProfileCancelDialog}
                      onOpenChange={setShowProfileCancelDialog}
                    >
                      <AlertDialogContent className="border bg-card">
                        <AlertDialogHeader>
                          <AlertDialogTitle className="text-foreground">
                            Discard Changes?
                          </AlertDialogTitle>
                          <AlertDialogDescription className="text-muted-foreground">
                            Are you sure you want to discard your changes? This action cannot be
                            undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Keep Editing</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={handleCancelProfileChanges}
                            className="bg-red-600 text-white hover:bg-red-700"
                          >
                            Discard Changes
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account">
            <Card className="border bg-card">
              <CardHeader>
                <CardTitle className="text-lg text-foreground sm:text-xl">
                  Account Details
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground sm:text-sm">
                  Update your username
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAccountUpdate} className="space-y-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="username" className="text-sm text-foreground sm:text-base">
                      Username
                    </Label>
                    <Input
                      id="username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={isAccountLoading}
                      className="text-sm"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="email" className="text-sm text-foreground sm:text-base">
                      Email
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={isAccountLoading}
                      className="text-sm"
                    />
                    {email !== user?.email && (
                      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 dark:border-blue-500/30 dark:bg-blue-900/20">
                        <div className="flex items-start gap-2">
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
                          <p className="text-xs text-blue-900 sm:text-sm dark:text-blue-200">
                            Changing your email will require verification. You&apos;ll be logged out
                            of unverified sessions.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Email Verification Status */}
                  <div className="rounded-lg border p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        {user?.is_verified ? (
                          <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-green-600" />
                        ) : (
                          <Mail className="mt-0.5 h-5 w-5 flex-shrink-0 text-purple-600" />
                        )}
                        <div className="space-y-1">
                          <p className="text-sm font-medium">
                            {user?.is_verified ? "Email Verified" : "Email Not Verified"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {user?.is_verified
                              ? "Your email address has been verified"
                              : "Please verify your email address to access all features"}
                          </p>
                        </div>
                      </div>
                      {!user?.is_verified && (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={handleResendVerification}
                          disabled={isResendingVerification}
                          className="flex-shrink-0"
                        >
                          {isResendingVerification ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Sending...
                            </>
                          ) : (
                            "Resend Email"
                          )}
                        </Button>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <Button
                      type="submit"
                      className="flex-1 bg-purple-600 text-sm text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50 sm:text-base"
                      disabled={isAccountLoading || !hasAccountChanges}
                    >
                      {isAccountLoading ? "Updating..." : "Update Account"}
                    </Button>
                    {hasAccountChanges && (
                      <Button
                        type="button"
                        onClick={() => setShowAccountCancelDialog(true)}
                        disabled={isAccountLoading}
                        variant="outline"
                        className="flex-1 border-red-900/50 text-sm text-red-400 hover:bg-red-900/20 hover:text-red-300 sm:text-base"
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </form>

                {/* Account Cancel Dialog */}
                <AlertDialog
                  open={showAccountCancelDialog}
                  onOpenChange={setShowAccountCancelDialog}
                >
                  <AlertDialogContent className="border bg-card">
                    <AlertDialogHeader>
                      <AlertDialogTitle className="text-foreground">
                        Discard Changes?
                      </AlertDialogTitle>
                      <AlertDialogDescription className="text-muted-foreground">
                        Are you sure you want to discard your changes? This action cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Keep Editing</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleCancelAccountChanges}
                        className="bg-red-600 text-white hover:bg-red-700"
                      >
                        Discard Changes
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </CardContent>
            </Card>

            <Separator className="my-4 sm:my-6" />

            {/* Delete Account Section */}
            <Card className="border border-red-900/50 bg-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base text-red-500 sm:text-lg">
                  <AlertTriangle className="h-4 w-4" />
                  Danger Zone
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground sm:text-sm">
                  Permanently delete your account and all associated data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="destructive"
                      className="w-full text-xs transition-all hover:scale-[1.02] hover:shadow-lg sm:text-sm"
                      disabled={isDeleting}
                    >
                      <Trash2 className="mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                      Delete Account
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="mx-4 max-w-md border bg-card">
                    <AlertDialogHeader>
                      <AlertDialogTitle className="text-base text-foreground sm:text-lg">
                        Are you absolutely sure?
                      </AlertDialogTitle>
                      <AlertDialogDescription className="text-xs text-muted-foreground">
                        This action cannot be undone. This will permanently delete your account, all
                        your listings, and remove all your data from our servers.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel className="text-xs sm:text-sm">Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleDeleteAccount}
                        className="bg-red-600 text-xs text-white hover:bg-red-700 sm:text-sm"
                      >
                        {isDeleting ? "Deleting..." : "Delete Account"}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <Card className="border bg-card">
              <CardHeader>
                <CardTitle className="text-lg text-foreground sm:text-xl">
                  Change Password
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground sm:text-sm">
                  Update your password to keep your account secure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordChange} className="space-y-3">
                  <div className="space-y-1.5">
                    <Label
                      htmlFor="current-password"
                      className="text-sm text-foreground sm:text-base"
                    >
                      Current Password
                    </Label>
                    <Input
                      id="current-password"
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      disabled={isPasswordLoading}
                      className="text-sm"
                      placeholder="Enter current password"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="new-password" className="text-sm text-foreground sm:text-base">
                      New Password
                    </Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      disabled={isPasswordLoading}
                      className="text-sm"
                      placeholder="Enter new password"
                    />

                    {/* Password strength indicator */}
                    {newPassword.length > 0 && (
                      <div className="space-y-1">
                        <div className="flex gap-1">
                          {[...Array(4)].map((_, i) => (
                            <div
                              key={i}
                              className={`h-1 flex-1 rounded-full transition-colors ${
                                i < passwordStrength ? strengthInfo.color : "bg-muted"
                              }`}
                            />
                          ))}
                        </div>
                        <p className="text-xs text-muted-foreground sm:text-sm">
                          Password strength: {strengthInfo.label}
                        </p>
                      </div>
                    )}

                    <p className="text-xs text-muted-foreground sm:text-sm">
                      Must be at least 8 characters
                    </p>
                  </div>

                  <div className="space-y-1.5">
                    <Label
                      htmlFor="confirm-password"
                      className="text-sm text-foreground sm:text-base"
                    >
                      Confirm New Password
                    </Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isPasswordLoading}
                      className="text-sm"
                      placeholder="Confirm new password"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="mt-4 w-full bg-purple-600 text-sm text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50 sm:text-base"
                    disabled={
                      isPasswordLoading || !currentPassword || !newPassword || !confirmPassword
                    }
                  >
                    {isPasswordLoading ? "Changing Password..." : "Change Password"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <SettingsContent />
    </ProtectedRoute>
  );
}
