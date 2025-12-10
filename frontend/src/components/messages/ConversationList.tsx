/**
 * Conversation list component showing all user conversations
 */

"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { createConversationsQueryOptions } from "@/queryOptions/createMessagingQueryOptions";
import { createUserQueryOptions } from "@/queryOptions/createUserQueryOptions";
import { ConversationPublic } from "@/types/message";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Loader2, AlertCircle, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import { API_BASE_URL } from "@/lib/constants";
import { useEffect } from "react";

interface ConversationListProps {
  selectedConversationId?: string;
  onSelectConversation: (conversationId: string, otherUserId: string) => void;
}

export function ConversationList({
  selectedConversationId,
  onSelectConversation,
}: ConversationListProps) {
  const { user } = useAuth();
  const router = useRouter();

  const {
    data: conversations,
    isLoading,
    error,
    refetch,
  } = useQuery(createConversationsQueryOptions());

  // Handle session expiration
  useEffect(() => {
    if (error instanceof Error && error.message === "SESSION_EXPIRED") {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user");
      router.push("/login?redirect=/messages");
    }
  }, [error, router]);

  // Get the other user ID for each conversation
  const getOtherUserId = (conversation: ConversationPublic): string => {
    return conversation.user_1_id === user?.id ? conversation.user_2_id : conversation.user_1_id;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-8">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <div className="text-center">
          <p className="font-semibold">Failed to load conversations</p>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
        <Button
          onClick={() => refetch()}
          variant="outline"
          size="sm"
          aria-label="Retry loading conversations"
        >
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-background">
        <h2 className="font-semibold text-lg">Messages</h2>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations && conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
            <MessageSquare className="h-16 w-16 text-muted-foreground" />
            <div>
              <p className="font-semibold">No conversations yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Message a seller from a listing to start a conversation
              </p>
            </div>
          </div>
        ) : (
          <div className="divide-y">
            {conversations?.map((conversation) => {
              const otherUserId = getOtherUserId(conversation);
              const isSelected = conversation.id === selectedConversationId;

              return (
                <ConversationListItem
                  key={conversation.id}
                  conversation={conversation}
                  otherUserId={otherUserId}
                  isSelected={isSelected}
                  onClick={() => onSelectConversation(conversation.id, otherUserId)}
                />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

interface ConversationListItemProps {
  conversation: ConversationPublic;
  otherUserId: string;
  isSelected: boolean;
  onClick: () => void;
}

function ConversationListItem({
  conversation,
  otherUserId,
  isSelected,
  onClick,
}: ConversationListItemProps) {
  const { data: otherUser } = useQuery(createUserQueryOptions(otherUserId));

  // Fetch profile data to get profile picture timestamp
  const { data: otherUserProfile } = useQuery({
    queryKey: ["profile", otherUserId],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/${otherUserId}/profile`);
        if (!response.ok) return null;
        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!otherUserId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  // Check if conversation has messages
  const { data: hasMessages } = useQuery({
    queryKey: ["conversationHasMessages", conversation.id],
    queryFn: async () => {
      try {
        const token = localStorage.getItem("auth_token");
        if (!token) return false;

        const response = await fetch(
          `${API_BASE_URL}/messages/conversations/${conversation.id}/messages?limit=1`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        if (!response.ok) return false;
        const messages = await response.json();
        return Array.isArray(messages) && messages.length > 0;
      } catch {
        return false;
      }
    },
    enabled: !!conversation.id && !conversation.last_message,
    staleTime: 1000 * 60, // 1 minute
  });

  const displayName = otherUser?.username || "Unknown User";
  const createdAt = new Date(conversation.created_at);
  const timeString = createdAt.toLocaleDateString([], {
    month: "short",
    day: "numeric",
  });

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 p-4 hover:bg-muted/50 transition-colors text-left focus:outline-none focus:ring-2 focus:ring-primary",
        isSelected && "bg-muted"
      )}
      aria-label={`Conversation with ${displayName}`}
      aria-current={isSelected ? "true" : undefined}
    >
      <Avatar className="h-12 w-12 shrink-0">
        <AvatarImage
          src={
            getProfilePictureUrl(
              otherUserProfile?.profile_picture_url,
              otherUserProfile?.profile_picture_updated_at
            ) || undefined
          }
          alt={displayName}
          loading="lazy"
        />
        <AvatarFallback>{displayName[0]?.toUpperCase()}</AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <p className="font-semibold truncate">{displayName}</p>
          <span className="text-xs text-muted-foreground shrink-0">{timeString}</span>
        </div>
        <p className="text-sm text-muted-foreground truncate">
          {conversation.last_message && conversation.last_message.trim() !== ""
            ? conversation.last_message
            : hasMessages
              ? "Continue conversation"
              : "Start a conversation"}
        </p>
      </div>

      {conversation.unread_count && conversation.unread_count > 0 && (
        <div className="shrink-0 h-5 min-w-5 rounded-full bg-primary text-primary-foreground text-xs font-semibold flex items-center justify-center px-1.5">
          {conversation.unread_count}
        </div>
      )}
    </button>
  );
}
