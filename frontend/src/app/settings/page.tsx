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
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken, setStoredUser } from "@/lib/auth";
import type { ProfilePublic, ContactInfo } from "@/types/user";

interface ProfileUpdatePayload {
  name?: string | null;
  campus?: string | null;
  contact_info?: ContactInfo;
}

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  // Profile state
  const [name, setName] = useState("");
  const [campus, setCampus] = useState("");
  const [phone, setPhone] = useState("");
  const [phoneError, setPhoneError] = useState("");
  const [originalProfile, setOriginalProfile] = useState<ProfilePublic | null>(null);
  const [profilePictureUrl, setProfilePictureUrl] = useState("");
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
        updates.contact_info = {
          email: user?.email,
          phone: phone.trim() || undefined,
        };
      }

      // If no changes, don't send request
      if (Object.keys(updates).length === 0) {
        toast.info("No changes to save");
        setIsProfileLoading(false);
        return;
      }

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
      const message = error instanceof Error ? error.message : "Failed to save profile";
      toast.error(message);
    } finally {
      setIsProfileLoading(false);
    }
  };

  const handlePictureUpdate = async () => {
    if (!profilePictureUrl.trim()) {
      toast.error("Please enter a profile picture URL");
      return;
    }

    setIsPictureLoading(true);

    try {
      const token = getAuthToken();
      if (!token) throw new Error("Not authenticated");

      const response = await fetch(`${API_BASE_URL}/users/profile/picture/`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          picture_url: profilePictureUrl.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to update profile picture");
      }

      toast.success("Profile picture updated successfully!", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });
      setProfilePictureUrl("");
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

      // Show success message before logout
      toast.success("Account deleted successfully", {
        style: {
          background: "rgb(20, 83, 45)",
          color: "white",
          border: "1px solid rgb(34, 197, 94)",
        },
      });

      // Use logout from AuthContext to properly clear state and redirect
      logout();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete account";
      toast.error(message);
      setIsDeleting(false);
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
                      <div className="flex flex-col sm:flex-row items-start gap-4 sm:gap-6">
                        <div className="flex-shrink-0">
                          <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gradient-to-br from-purple-500/20 to-purple-600/20 rounded-full flex items-center justify-center border border-purple-500/20">
                            <UserIcon className="w-10 h-10 sm:w-12 sm:h-12 text-purple-300" />
                          </div>
                        </div>
                        <div className="flex-1 w-full space-y-3">
                          <div>
                            <Label
                              htmlFor="profilePicture"
                              className="text-base sm:text-lg text-gray-200"
                            >
                              Profile Picture URL
                            </Label>
                            <p className="text-xs sm:text-sm text-gray-500 mt-1">
                              Enter a URL to your profile picture (e.g., from Imgur, Gravatar, etc.)
                            </p>
                          </div>
                          <div className="flex flex-col sm:flex-row gap-2">
                            <Input
                              id="profilePicture"
                              type="url"
                              placeholder="https://example.com/your-image.jpg"
                              value={profilePictureUrl}
                              onChange={(e) => setProfilePictureUrl(e.target.value)}
                              disabled={isPictureLoading}
                              className="bg-gray-950 border-gray-700 text-white text-base placeholder:text-gray-600"
                            />
                            <Button
                              type="button"
                              onClick={handlePictureUpdate}
                              disabled={isPictureLoading || !profilePictureUrl.trim()}
                              className="bg-purple-600 hover:bg-purple-700 shrink-0 w-full sm:w-auto"
                            >
                              <Upload className="w-4 h-4 mr-2" />
                              {isPictureLoading ? "Uploading..." : "Upload"}
                            </Button>
                          </div>
                        </div>
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
                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 sm:p-4">
                  <p className="text-blue-300 text-sm sm:text-base">
                    🔧 Password change functionality is coming soon. This feature requires backend
                    implementation.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
