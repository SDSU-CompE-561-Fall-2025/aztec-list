/**
 * New conversation dialog for starting conversations
 */

"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
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
import { API_BASE_URL, STATIC_BASE_URL } from "@/lib/constants";
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

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
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
  };

  const handleStartConversation = () => {
    if (selectedUser) {
      createConversationMutation.mutate(selectedUser.id);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Conversation</DialogTitle>
          <DialogDescription>Search for a user to start a conversation</DialogDescription>
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
            <div className="flex items-center gap-3 p-3 rounded-lg border bg-muted">
              <Avatar className="h-10 w-10">
                <AvatarImage
                  src={`${STATIC_BASE_URL}${getProfilePictureUrl(selectedUser.id, undefined)}`}
                  alt={selectedUser.username}
                  loading="lazy"
                />
                <AvatarFallback>{selectedUser.username[0]?.toUpperCase()}</AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="font-semibold truncate">{selectedUser.username}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setSelectedUser(null)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          )}

          {/* Search Results */}
          {!selectedUser && searchResults.length > 0 && (
            <div className="border rounded-lg divide-y max-h-64 overflow-y-auto">
              {searchResults.map((user) => (
                <button
                  key={user.id}
                  onClick={() => {
                    setSelectedUser(user);
                    setSearchResults([]);
                    setSearchQuery("");
                  }}
                  className="w-full flex items-center gap-3 p-3 hover:bg-muted transition-colors text-left focus:outline-none focus:ring-2 focus:ring-primary"
                  aria-label={`Select ${user.username}`}
                >
                  <Avatar className="h-10 w-10">
                    <AvatarImage
                      src={`${STATIC_BASE_URL}${getProfilePictureUrl(user.id, undefined)}`}
                      alt={user.username}
                      loading="lazy"
                    />
                    <AvatarFallback>{user.username[0]?.toUpperCase()}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold truncate">{user.username}</p>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* No Results */}
          {!selectedUser && searchQuery && !isSearching && searchResults.length === 0 && (
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
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleStartConversation}
              disabled={!selectedUser || createConversationMutation.isPending}
              className="flex-1"
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
