/**
 * New conversation dialog for starting conversations
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Loader2, Search, X } from "lucide-react";
import { createOrGetConversation } from "@/lib/messaging-api";
import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import { UserPublic } from "@/types/user";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";

interface NewConversationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConversationCreated?: (conversationId: string, otherUserId: string) => void;
}

export function NewConversationDialog({
  open,
  onOpenChange,
  onConversationCreated,
}: NewConversationDialogProps) {
  const { user: currentUser } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUser, setSelectedUser] = useState<UserPublic | null>(null);
  const [searchResults, setSearchResults] = useState<UserPublic[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }

    setIsSearching(true);
    setHasSearched(true);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${API_BASE_URL}/users/?search=${encodeURIComponent(searchQuery)}&limit=10`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to search users");
      }

      const data = await response.json();
      const users = Array.isArray(data) ? data : data.users || [];

      // Filter out current user
      const filteredUsers = users.filter((u: UserPublic) => u.id !== currentUser?.id);
      setSearchResults(filteredUsers);
    } catch (error) {
      console.error("Search error:", error);
      toast.error("Failed to search users");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, [searchQuery, currentUser?.id]);

  // Debounced search effect - automatically search as user types
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setHasSearched(false);
      return;
    }

    const debounceTimer = setTimeout(() => {
      handleSearch();
    }, 400); // Wait 400ms after user stops typing

    return () => clearTimeout(debounceTimer);
  }, [searchQuery, handleSearch]);

  const createConversationMutation = useMutation({
    mutationFn: (otherUserId: string) => createOrGetConversation(otherUserId),
    onSuccess: (conversation) => {
      const otherUserId =
        conversation.user_1_id === currentUser?.id
          ? conversation.user_2_id
          : conversation.user_1_id;

      toast.success("Conversation ready");
      onOpenChange(false);
      setSearchQuery("");
      setSelectedUser(null);
      setSearchResults([]);

      if (onConversationCreated) {
        onConversationCreated(conversation.id, otherUserId);
      }
    },
    onError: (error) => {
      toast.error(error instanceof Error ? error.message : "Failed to create conversation");
    },
  });

  const handleStartConversation = () => {
    if (selectedUser) {
      createConversationMutation.mutate(selectedUser.id);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl">New Conversation</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Search for a user to start a conversation
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search Input */}
          <div className="space-y-2">
            <Label htmlFor="search">Search by username or email</Label>
            <div className="flex gap-2">
              <Input
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Enter username or email..."
                aria-label="Search for users"
                autoComplete="off"
              />
              <Button
                onClick={handleSearch}
                disabled={isSearching || !searchQuery.trim()}
                size="icon"
                className="bg-purple-600 hover:bg-purple-700 text-white"
                aria-label="Search users"
              >
                {isSearching ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Search className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Selected User */}
          {selectedUser && (
            <SelectedUserDisplay user={selectedUser} onClear={() => setSelectedUser(null)} />
          )}

          {/* Search Results */}
          {!selectedUser && searchResults.length > 0 && (
            <div className="border rounded-lg divide-y max-h-64 overflow-y-auto">
              {searchResults.map((user) => (
                <UserSearchResultItem
                  key={user.id}
                  user={user}
                  onClick={() => {
                    setSelectedUser(user);
                    setSearchResults([]);
                    setSearchQuery("");
                  }}
                />
              ))}
            </div>
          )}

          {/* No Results */}
          {!selectedUser && hasSearched && !isSearching && searchResults.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">No users found</p>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-4">
            <Button
              variant="outline"
              onClick={() => {
                onOpenChange(false);
                setSearchQuery("");
                setSelectedUser(null);
                setSearchResults([]);
                setHasSearched(false);
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleStartConversation}
              disabled={!selectedUser || createConversationMutation.isPending}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
            >
              {createConversationMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Creating...
                </>
              ) : (
                "Start Conversation"
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Helper component to display selected user with profile picture
function SelectedUserDisplay({ user, onClear }: { user: UserPublic; onClear: () => void }) {
  const { data: profile } = useQuery({
    queryKey: ["profile", user.id],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/${user.id}/profile`);
        if (!response.ok) return null;
        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!user.id,
    staleTime: 1000 * 60 * 5,
  });

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-muted">
      <Avatar className="h-10 w-10">
        <AvatarImage
          src={getProfilePictureUrl(profile?.profile_picture_url, profile?.updated_at) || undefined}
          alt={user.username}
          loading="lazy"
        />
        <AvatarFallback>{user.username[0]?.toUpperCase()}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <p className="font-semibold truncate">{user.username}</p>
      </div>
      <Button variant="ghost" size="icon" onClick={onClear}>
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

// Helper component for search result item with profile picture
function UserSearchResultItem({ user, onClick }: { user: UserPublic; onClick: () => void }) {
  const { data: profile } = useQuery({
    queryKey: ["profile", user.id],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/${user.id}/profile`);
        if (!response.ok) return null;
        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!user.id,
    staleTime: 1000 * 60 * 5,
  });

  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 p-3 hover:bg-muted transition-colors text-left focus:outline-none focus:ring-2 focus:ring-primary"
      aria-label={`Select ${user.username}`}
    >
      <Avatar className="h-10 w-10">
        <AvatarImage
          src={getProfilePictureUrl(profile?.profile_picture_url, profile?.updated_at) || undefined}
          alt={user.username}
          loading="lazy"
        />
        <AvatarFallback>{user.username[0]?.toUpperCase()}</AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <p className="font-semibold truncate">{user.username}</p>
      </div>
    </button>
  );
}
