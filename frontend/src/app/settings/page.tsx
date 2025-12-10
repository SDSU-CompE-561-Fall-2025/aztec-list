"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import { toast } from "sonner";
import { ChevronLeft, Trash2, AlertTriangle, Upload } from "lucide-react";

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
import { getAuthToken, setStoredUser, changePassword } from "@/lib/auth";
import { showErrorToast } from "@/lib/errorHandling";
import { createProfileQueryOptions } from "@/queryOptions/createProfileQueryOptions";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import type { ContactInfo } from "@/types/user";

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

  // Fetch existing profile data using React Query
  const { data: profile, isLoading: isProfileFetching } = useQuery(
    createProfileQueryOptions(user?.id)
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
    [formName, formCampus, formPhone, profile, stagedPictureFile, isPictureRemovalStaged]
  );

  // Check if form is valid for submission
  const isFormValid = useMemo(() => !phoneError, [phoneError]);

  // Account state
  const [username, setUsername] = useState(user?.username ?? "");
  const [isAccountLoading, setIsAccountLoading] = useState(false);

  // Track if account has changes (memoized)
  const hasAccountChanges = useMemo(
    () => username !== (user?.username ?? ""),
    [username, user?.username]
  );

  // Delete account state
  const [isDeleting, setIsDeleting] = useState(false);

  // Cancel confirmation dialogs
  const [showProfileCancelDialog, setShowProfileCancelDialog] = useState(false);
  const [showAccountCancelDialog, setShowAccountCancelDialog] = useState(false);

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isPasswordLoading, setIsPasswordLoading] = useState(false);

  // Initialize username from user data
  useEffect(() => {
    if (user?.username) {
      setUsername(user.username);
    }
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
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");

      // Step 1: Handle profile picture upload if staged
      if (stagedPictureFile) {
        const formData = new FormData();
        formData.append("file", stagedPictureFile);

        const pictureResponse = await fetch(`${API_BASE_URL}/users/profile/picture`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (!pictureResponse.ok) {
          const errorData = await pictureResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || "Failed to upload profile picture");
        }
      }

      // Step 2: Handle profile picture removal if staged
      if (isPictureRemovalStaged) {
        const removeResponse = await fetch(`${API_BASE_URL}/users/profile/`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            profile_picture_url: null,
          }),
        });

        if (!removeResponse.ok) {
          const errorData = await removeResponse.json().catch(() => ({}));
          throw new Error(errorData.detail || "Failed to remove profile picture");
        }
      }

      // Step 3: Update other profile fields
      const updates: ProfileUpdatePayload = {};

      if (formName !== (profile?.name || "")) {
        updates.name = formName.trim() || null;
      }

      if (formCampus !== (profile?.campus || "")) {
        updates.campus = formCampus.trim() || null;
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
        const response = await fetch(`${API_BASE_URL}/users/profile/`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(updates),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || "Failed to save profile");
        }
      }

      // Fetch updated profile to get latest data with fresh updated_at timestamp
      // This is done regardless of whether fields were updated, since picture changes also need refresh
      const profileResponse = await fetch(`${API_BASE_URL}/users/profile/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (profileResponse.ok) {
        const updatedProfile = await profileResponse.json();

        // Update the React Query cache with fresh data from server
        // This triggers all components using this query to re-render with new updated_at
        queryClient.setQueryData(["profile", user?.id], updatedProfile);

        // Update form fields to match the saved data
        setFormName(updatedProfile.name || "");
        setFormCampus(updatedProfile.campus || "");
        setFormPhone(updatedProfile.contact_info?.phone || "");
      }

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

      if (username === user?.username) {
        toast.info("No changes to save");
        setIsAccountLoading(false);
        return;
      }

      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ username }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update account");
      }

      // Get updated user data from response
      const updatedUser = await response.json();

      // Update localStorage - this will automatically sync AuthContext via custom event
      setStoredUser(updatedUser);

      // Invalidate all queries that might display the username
      queryClient.invalidateQueries({ queryKey: ["user"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });

      toast.success("Account updated successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
    } catch (error) {
      // Reset username to original value on error
      setUsername(user?.username ?? "");
      showErrorToast(error, "Failed to update account");
    } finally {
      setIsAccountLoading(false);
    }
  };

  const handleCancelAccountChanges = () => {
    // Reset username to original value
    setUsername(user?.username ?? "");
    setShowAccountCancelDialog(false);
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
      <div className="max-w-2xl mx-auto w-full">
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          <Button
            variant="ghost"
            className="text-muted-foreground hover:text-foreground -ml-3 mb-3"
            onClick={() => router.push("/profile")}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back to Profile
          </Button>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-1">Account Settings</h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Manage your account preferences and information
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="profile" className="space-y-3 sm:space-y-4">
          <TabsList className="bg-muted border w-full grid grid-cols-3 h-auto p-1">
            <TabsTrigger
              value="profile"
              className="text-xs sm:text-sm data-[state=active]:bg-background"
            >
              Profile
            </TabsTrigger>
            <TabsTrigger
              value="account"
              className="text-xs sm:text-sm data-[state=active]:bg-background"
            >
              Account
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="text-xs sm:text-sm data-[state=active]:bg-background"
            >
              Security
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card className="bg-card border">
              <CardHeader>
                <CardTitle className="text-lg sm:text-xl text-foreground">
                  Profile Information
                </CardTitle>
                <CardDescription className="text-sm sm:text-base text-muted-foreground">
                  Add details to help buyers connect with you
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isInitialLoading ? (
                  <div className="animate-pulse">
                    {/* Profile Picture Skeleton */}
                    <div className="mb-6 pb-6 border-b">
                      <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-muted rounded-full"></div>
                        <div className="flex gap-2">
                          <div className="h-8 w-24 bg-muted rounded"></div>
                          <div className="h-8 w-24 bg-muted rounded"></div>
                        </div>
                      </div>
                    </div>
                    {/* Form Fields Skeleton - wrapped in space-y-4 to match form */}
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <div className="h-6 w-24 bg-muted rounded"></div>
                        <div className="h-9 bg-muted rounded"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-6 w-16 bg-muted rounded"></div>
                        <div className="h-9 bg-muted rounded"></div>
                        <div className="h-5 w-20 bg-muted rounded"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-6 w-28 bg-muted rounded"></div>
                        <div className="h-9 bg-muted rounded"></div>
                        <div className="h-5 w-52 bg-muted rounded"></div>
                      </div>
                      <div className="h-9 w-full bg-muted rounded"></div>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Profile Picture Section */}
                    <div className="mb-6 pb-6 border-b">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="w-16 h-16 bg-gradient-to-br from-purple-500/20 to-purple-600/20 border-2 border-purple-500/30 rounded-full flex items-center justify-center overflow-hidden relative group">
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
                            ) : profile?.profile_picture_url ? (
                              <Image
                                src={
                                  getProfilePictureUrl(
                                    profile.profile_picture_url,
                                    profile.updated_at
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
                              className="bg-purple-600 hover:bg-purple-700 text-white cursor-pointer"
                            >
                              <span>
                                <Upload className="w-4 h-4 mr-2" />
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
                                <Trash2 className="w-4 h-4 mr-2" />
                                Remove
                              </Button>
                            )}
                        </div>
                      </div>
                    </div>

                    <form onSubmit={handleProfileSave} className="space-y-3">
                      <div className="space-y-1.5">
                        <Label htmlFor="name" className="text-sm sm:text-base text-foreground">
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
                        <Label htmlFor="campus" className="text-sm sm:text-base text-foreground">
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
                        <Label htmlFor="phone" className="text-sm sm:text-base text-foreground">
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
                          <p className="text-xs sm:text-sm text-muted-foreground">
                            US format: (555) 123-4567
                          </p>
                        )}
                      </div>

                      <div className="flex gap-3 pt-2">
                        <Button
                          type="submit"
                          className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-sm sm:text-base disabled:opacity-50 disabled:cursor-not-allowed"
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
                            className="flex-1 border-red-900/50 text-red-400 hover:bg-red-900/20 hover:text-red-300 text-sm sm:text-base"
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
                      <AlertDialogContent className="bg-card border">
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
                            className="bg-red-600 hover:bg-red-700 text-white"
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
            <Card className="bg-card border">
              <CardHeader>
                <CardTitle className="text-lg sm:text-xl text-foreground">
                  Account Details
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm text-muted-foreground">
                  Update your username
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAccountUpdate} className="space-y-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="username" className="text-sm sm:text-base text-foreground">
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
                    <Label htmlFor="email-display" className="text-sm sm:text-base text-foreground">
                      Email
                    </Label>
                    <Input
                      id="email-display"
                      type="email"
                      value={user?.email ?? ""}
                      disabled
                      className="text-sm cursor-not-allowed opacity-60"
                    />
                    <p className="text-xs sm:text-sm text-muted-foreground">
                      Email cannot be changed at this time
                    </p>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <Button
                      type="submit"
                      className="flex-1 bg-purple-600 hover:bg-purple-700 text-white text-sm sm:text-base disabled:opacity-50 disabled:cursor-not-allowed"
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
                        className="flex-1 border-red-900/50 text-red-400 hover:bg-red-900/20 hover:text-red-300 text-sm sm:text-base"
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
                  <AlertDialogContent className="bg-card border">
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
                        className="bg-red-600 hover:bg-red-700 text-white"
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
            <Card className="bg-card border border-red-900/50">
              <CardHeader>
                <CardTitle className="text-base sm:text-lg text-red-500 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Danger Zone
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm text-muted-foreground">
                  Permanently delete your account and all associated data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="destructive"
                      className="w-full text-xs sm:text-sm transition-all hover:scale-[1.02] hover:shadow-lg"
                      disabled={isDeleting}
                    >
                      <Trash2 className="w-3 h-3 sm:w-4 sm:h-4 mr-2" />
                      Delete Account
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="bg-card border max-w-md mx-4">
                    <AlertDialogHeader>
                      <AlertDialogTitle className="text-base sm:text-lg text-foreground">
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
                        className="bg-red-600 hover:bg-red-700 text-xs sm:text-sm"
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
            <Card className="bg-card border">
              <CardHeader>
                <CardTitle className="text-lg sm:text-xl text-foreground">
                  Change Password
                </CardTitle>
                <CardDescription className="text-xs sm:text-sm text-muted-foreground">
                  Update your password to keep your account secure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordChange} className="space-y-3">
                  <div className="space-y-1.5">
                    <Label
                      htmlFor="current-password"
                      className="text-sm sm:text-base text-foreground"
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
                    <Label htmlFor="new-password" className="text-sm sm:text-base text-foreground">
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
                    <p className="text-xs sm:text-sm text-muted-foreground">
                      Must be at least 8 characters
                    </p>
                  </div>

                  <div className="space-y-1.5">
                    <Label
                      htmlFor="confirm-password"
                      className="text-sm sm:text-base text-foreground"
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
                    className="w-full bg-purple-600 hover:bg-purple-700 text-white text-sm sm:text-base disabled:opacity-50 disabled:cursor-not-allowed mt-4"
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
