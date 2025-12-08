"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ChevronLeft, Trash2, AlertTriangle, Upload, User as UserIcon } from "lucide-react";

import { useAuth } from "@/contexts/AuthContext";
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
import { API_BASE_URL, STATIC_BASE_URL } from "@/lib/constants";
import { getAuthToken, setStoredUser, changePassword } from "@/lib/auth";
import type { ProfilePublic, ContactInfo } from "@/types/user";

interface ProfileUpdatePayload {
  name?: string | null;
  campus?: string | null;
  contact_info?: ContactInfo;
}

// Helper function to build full URL for profile picture
const getProfilePictureUrl = (path: string | null | undefined): string | null => {
  if (!path) return null;
  // Add cache-busting timestamp to force browser to reload the image
  const timestamp = Date.now();
  // If already a full URL, return as-is with timestamp
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return `${path}?t=${timestamp}`;
  }
  // Build full URL from relative path with timestamp
  return `${STATIC_BASE_URL}${path}?t=${timestamp}`;
};

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  // Profile state
  const [name, setName] = useState("");
  const [campus, setCampus] = useState("");
  const [phone, setPhone] = useState("");
  const [phoneError, setPhoneError] = useState("");
  const [originalProfile, setOriginalProfile] = useState<ProfilePublic | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  const [isPictureLoading, setIsPictureLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  // Fetch existing profile data
  useEffect(() => {
    const fetchProfile = async () => {
      const token = getAuthToken();
      if (!token) {
        setIsInitialLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/users/profile/`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data: ProfilePublic = await response.json();
          setOriginalProfile(data);
          setName(data.name || "");
          setCampus(data.campus || "");
          setPhone(data.contact_info?.phone || "");
        }
      } catch {
        // Profile doesn't exist yet, that's okay
      } finally {
        setIsInitialLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // Track if profile has changes (memoized to avoid unnecessary recalculations)
  const hasProfileChanges = useMemo(
    () =>
      name !== (originalProfile?.name || "") ||
      campus !== (originalProfile?.campus || "") ||
      phone !== (originalProfile?.contact_info?.phone || ""),
    [name, campus, phone, originalProfile]
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
    setPhone(formatted);
    validatePhoneNumber(formatted);
  };

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate phone before submitting
    if (!validatePhoneNumber(phone)) {
      toast.error("Please enter a valid phone number or leave it empty");
      return;
    }

    setIsProfileLoading(true);

    try {
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");

      // Build update object with only changed fields
      const updates: ProfileUpdatePayload = {};

      if (name !== (originalProfile?.name || "")) {
        updates.name = name.trim() || null;
      }

      if (campus !== (originalProfile?.campus || "")) {
        updates.campus = campus.trim() || null;
      }

      const originalPhone = originalProfile?.contact_info?.phone || "";
      if (phone !== originalPhone) {
        if (!user?.email) {
          throw new Error("User email not available");
        }
        updates.contact_info = {
          email: user.email,
          phone: phone.trim() || undefined,
        };
      }

      // If no changes, don't send request
      if (Object.keys(updates).length === 0) {
        toast.info("No changes to save");
        setIsProfileLoading(false);
        return;
      }

      console.log("Sending profile update:", updates);
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
        console.error("Profile update error:", errorData);
        throw new Error(errorData.detail || "Failed to save profile");
      }

      const updatedProfile = await response.json();
      setOriginalProfile(updatedProfile);
      toast.success("Profile saved successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
    } catch (error) {
      console.error("Profile save error:", error);
      const message = error instanceof Error ? error.message : "Failed to save profile";
      toast.error(message);
    } finally {
      setIsProfileLoading(false);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file");
      return;
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image must be smaller than 5MB");
      return;
    }

    setSelectedFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);

    // Automatically upload the file
    await handlePictureUpload(file);
  };

  const handlePictureUpload = async (file: File) => {
    setIsPictureLoading(true);

    try {
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");

      const formData = new FormData();
      formData.append("file", file);

      console.log("Uploading profile picture:", file.name, file.size);
      const response = await fetch(`${API_BASE_URL}/users/profile/picture`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("Picture upload error:", errorData);
        throw new Error(errorData.detail || "Failed to update profile picture");
      }

      const updatedProfile = await response.json();
      setOriginalProfile(updatedProfile);

      toast.success("Profile picture updated successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });

      // Clear selected file but keep preview until page refreshes
      setSelectedFile(null);
      // Don't clear previewUrl immediately - it will be replaced by the new profile picture
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to update profile picture";
      toast.error(message);
    } finally {
      setIsPictureLoading(false);
    }
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

      // Update stored user in localStorage
      setStoredUser(updatedUser);

      toast.success("Account updated successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });

      // Reload the page to refresh all components with new username
      window.location.reload();
    } catch (error) {
      // Reset username to original value on error
      setUsername(user?.username ?? "");
      const message = error instanceof Error ? error.message : "Failed to update account";
      toast.error(message, {
        duration: 5000,
        style: {
          background: "rgb(153, 27, 27)", // red-900
          color: "white",
          border: "1px solid rgb(220, 38, 38)", // red-600
        },
      });
    } finally {
      setIsAccountLoading(false);
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
      toast.success("Account deleted successfully");
      router.push("/");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete account";
      toast.error(message);
      setIsDeleting(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("All password fields are required");
      return;
    }

    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters");
      return;
    }

    if (newPassword === currentPassword) {
      toast.error("New password must be different from current password");
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match");
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
      const message = error instanceof Error ? error.message : "Failed to change password";
      toast.error(message, {
        duration: 5000,
        style: {
          background: "rgb(153, 27, 27)",
          color: "white",
          border: "1px solid rgb(220, 38, 38)",
        },
      });
    } finally {
      setIsPasswordLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <Button
            variant="ghost"
            className="text-gray-400 hover:text-gray-100 hover:bg-gray-800/50 -ml-3 mb-4"
            onClick={() => router.push("/profile")}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Back to Profile
          </Button>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">Account Settings</h1>
          <p className="text-gray-400 text-base sm:text-lg">
            Manage your account preferences and information
          </p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="profile" className="space-y-4 sm:space-y-6">
          <TabsList className="bg-gray-900 border border-gray-800 w-full grid grid-cols-3 h-auto p-1">
            <TabsTrigger
              value="profile"
              className="text-sm sm:text-base data-[state=active]:bg-gray-800"
            >
              Profile
            </TabsTrigger>
            <TabsTrigger
              value="account"
              className="text-sm sm:text-base data-[state=active]:bg-gray-800"
            >
              Account
            </TabsTrigger>
            <TabsTrigger
              value="security"
              className="text-sm sm:text-base data-[state=active]:bg-gray-800"
            >
              Security
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-xl sm:text-2xl text-white">
                  Profile Information
                </CardTitle>
                <CardDescription className="text-sm sm:text-base text-gray-400">
                  Add details to help buyers connect with you
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isInitialLoading ? (
                  <div className="space-y-4 animate-pulse">
                    <div className="h-24 bg-gray-800 rounded-lg"></div>
                    <div className="h-12 bg-gray-800 rounded"></div>
                    <div className="h-12 bg-gray-800 rounded"></div>
                    <div className="h-12 bg-gray-800 rounded"></div>
                  </div>
                ) : (
                  <>
                    {/* Profile Picture Section */}
                    <div className="mb-6 pb-6 border-b border-gray-800">
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden relative group">
                            {previewUrl || originalProfile?.profile_picture_url ? (
                              <img
                                src={
                                  previewUrl ||
                                  getProfilePictureUrl(originalProfile?.profile_picture_url) ||
                                  ""
                                }
                                alt="Profile"
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <span className="text-2xl font-medium text-gray-800">JD</span>
                            )}
                          </div>
                        </div>
                        <input
                          id="profilePictureFile"
                          type="file"
                          accept="image/*"
                          onChange={handleFileSelect}
                          disabled={isPictureLoading}
                          className="hidden"
                        />
                        <label htmlFor="profilePictureFile">
                          <Button
                            type="button"
                            asChild
                            disabled={isPictureLoading}
                            className="bg-purple-600 hover:bg-purple-700 cursor-pointer"
                          >
                            <span>
                              <Upload className="w-4 h-4 mr-2" />
                              {isPictureLoading ? "Uploading..." : "Upload Photo"}
                            </span>
                          </Button>
                        </label>
                      </div>
                    </div>

                    <form onSubmit={handleProfileSave} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="name" className="text-base sm:text-lg text-gray-200">
                          Full Name
                        </Label>
                        <Input
                          id="name"
                          type="text"
                          placeholder="John Doe"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          disabled={isProfileLoading}
                          className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="campus" className="text-base sm:text-lg text-gray-200">
                          Campus
                        </Label>
                        <Input
                          id="campus"
                          type="text"
                          placeholder="San Diego State University"
                          value={campus}
                          onChange={(e) => setCampus(e.target.value)}
                          disabled={isProfileLoading}
                          className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                        />
                        <p className="text-sm sm:text-base text-gray-500">Optional</p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="phone" className="text-base sm:text-lg text-gray-200">
                          Phone Number
                        </Label>
                        <Input
                          id="phone"
                          type="tel"
                          placeholder="(555) 123-4567"
                          value={phone}
                          onChange={handlePhoneChange}
                          disabled={isProfileLoading}
                          className={`bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600 ${
                            phoneError ? "border-red-500" : ""
                          }`}
                        />
                        {phoneError && <p className="text-sm text-red-500">{phoneError}</p>}
                        <p className="text-sm sm:text-base text-gray-500">
                          Optional - US format: (555) 123-4567
                        </p>
                      </div>

                      <Button
                        type="submit"
                        className="w-full bg-purple-600 hover:bg-purple-700 text-base sm:text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isProfileLoading || !hasProfileChanges || !isFormValid}
                      >
                        {isProfileLoading ? "Saving..." : "Save Profile"}
                      </Button>
                    </form>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Account Tab */}
          <TabsContent value="account">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-xl sm:text-2xl text-white">Account Details</CardTitle>
                <CardDescription className="text-sm sm:text-base text-gray-400">
                  Update your username
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAccountUpdate} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="username" className="text-base sm:text-lg text-gray-200">
                      Username
                    </Label>
                    <Input
                      id="username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      disabled={isAccountLoading}
                      className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email-display" className="text-base sm:text-lg text-gray-200">
                      Email
                    </Label>
                    <Input
                      id="email-display"
                      type="email"
                      value={user?.email ?? ""}
                      disabled
                      className="bg-gray-950 border-gray-700 text-gray-500 text-base cursor-not-allowed"
                    />
                    <p className="text-sm sm:text-base text-gray-500">
                      Email cannot be changed at this time
                    </p>
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-purple-600 hover:bg-purple-700 text-base sm:text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isAccountLoading || !hasAccountChanges}
                  >
                    {isAccountLoading ? "Updating..." : "Update Account"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Separator className="my-6 sm:my-8 bg-gray-800" />

            {/* Delete Account Section */}
            <Card className="bg-gray-900 border-red-900/50">
              <CardHeader>
                <CardTitle className="text-xl sm:text-2xl text-red-500 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6" />
                  Danger Zone
                </CardTitle>
                <CardDescription className="text-sm sm:text-base text-gray-400">
                  Permanently delete your account and all associated data
                </CardDescription>
              </CardHeader>
              <CardContent>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="destructive"
                      className="w-full text-base sm:text-lg transition-all hover:scale-[1.02] hover:shadow-lg"
                      disabled={isDeleting}
                    >
                      <Trash2 className="w-4 h-4 sm:w-5 sm:h-5 mr-2" />
                      Delete Account
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent className="bg-gray-900 border-gray-800 max-w-md mx-4">
                    <AlertDialogHeader>
                      <AlertDialogTitle className="text-xl sm:text-2xl text-white">
                        Are you absolutely sure?
                      </AlertDialogTitle>
                      <AlertDialogDescription className="text-sm sm:text-base text-gray-400">
                        This action cannot be undone. This will permanently delete your account, all
                        your listings, and remove all your data from our servers.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel className="text-sm sm:text-base">Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={handleDeleteAccount}
                        className="bg-red-600 hover:bg-red-700 text-sm sm:text-base"
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
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-xl sm:text-2xl text-white">Change Password</CardTitle>
                <CardDescription className="text-sm sm:text-base text-gray-400">
                  Update your password to keep your account secure
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordChange} className="space-y-4">
                  <div className="space-y-2">
                    <Label
                      htmlFor="current-password"
                      className="text-base sm:text-lg text-gray-200"
                    >
                      Current Password
                    </Label>
                    <Input
                      id="current-password"
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      disabled={isPasswordLoading}
                      className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                      placeholder="Enter current password"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="new-password" className="text-base sm:text-lg text-gray-200">
                      New Password
                    </Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      disabled={isPasswordLoading}
                      className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                      placeholder="Enter new password"
                    />
                    <p className="text-sm sm:text-base text-gray-500">
                      Must be at least 8 characters
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label
                      htmlFor="confirm-password"
                      className="text-base sm:text-lg text-gray-200"
                    >
                      Confirm New Password
                    </Label>
                    <Input
                      id="confirm-password"
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      disabled={isPasswordLoading}
                      className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                      placeholder="Confirm new password"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-purple-600 hover:bg-purple-700 text-base sm:text-lg disabled:opacity-50 disabled:cursor-not-allowed"
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
