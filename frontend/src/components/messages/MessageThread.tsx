/**
 * Message thread component displaying conversation messages
 */

"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createMessagesQueryOptions } from "@/queryOptions/createMessagingQueryOptions";
import { Message } from "@/types/message";
import { useWebSocket } from "@/hooks/useWebSocket";
import { MessageInput } from "./MessageInput";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Loader2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { getProfilePictureUrl } from "@/lib/profile-picture";
import { API_BASE_URL } from "@/lib/constants";
import { toast } from "sonner";

interface MessageThreadProps {
  conversationId: string;
  otherUserId: string;
  otherUserName: string;
}

export function MessageThread({ conversationId, otherUserId, otherUserName }: MessageThreadProps) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState(0);
  const [allMessages, setAllMessages] = useState<Message[]>([]);

  const {
    data: messages,
    isLoading,
    error,
  } = useQuery(createMessagesQueryOptions(conversationId, 50, offset));

  // Fetch profile data for profile pictures
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
    staleTime: 1000 * 60 * 5,
  });

  const { data: currentUserProfile } = useQuery({
    queryKey: ["profile", user?.id],
    queryFn: async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/users/${user?.id}/profile`);
        if (!response.ok) return null;
        return response.json();
      } catch {
        return null;
      }
    },
    enabled: !!user?.id,
    staleTime: 1000 * 60 * 5,
  });

  // Memoize WebSocket callbacks to prevent reconnections
  const handleNewMessage = useCallback(
    (newMessage: Message) => {
      setAllMessages((prev) => {
        // Avoid duplicates
        if (prev.some((m) => m.id === newMessage.id)) {
          return prev;
        }
        return [...prev, newMessage];
      });

      // Invalidate queries to keep cache fresh across navigation
      queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });

      // Show notification if message is from other user and window is not focused
      if (newMessage.sender_id !== user?.id && !document.hasFocus()) {
        toast.info(`New message from ${otherUserName}`);
      }
    },
    [user?.id, otherUserName, conversationId, queryClient]
  );

  const handleConnectionError = useCallback((error: Event) => {
    // Only show error toast for max retries to avoid spam
    if (error.type === "Max reconnection attempts reached") {
      toast.error("Unable to connect. Please check your internet and refresh the page.");
    }
  }, []);

  // WebSocket for real-time messages
  const { isConnected, isConnecting, sendMessage } = useWebSocket({
    conversationId,
    onMessage: handleNewMessage,
    onError: handleConnectionError,
  });

  // Merge fetched messages with real-time messages using useMemo
  const displayMessages = useMemo(() => {
    if (!messages) return allMessages;

    const combined = [...messages, ...allMessages];
    // Remove duplicates and sort by created_at
    const unique = Array.from(new Map(combined.map((m) => [m.id, m])).values()).sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
    return unique;
  }, [messages, allMessages]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [displayMessages]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      // Allow sending if connected or if connection is being established
      // Messages will be queued and sent once connected
      if (!isConnected && !isConnecting) {
        toast.error("Connection lost. Reconnecting...");
        return;
      }

      try {
        sendMessage(content);
      } catch (error) {
        toast.error("Failed to send message. Please try again.");
        console.error("Send message error:", error);
      }
    },
    [isConnected, isConnecting, sendMessage]
  );

  const loadMoreMessages = () => {
    setOffset((prev) => prev + 50);
  };

  if (isLoading && allMessages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8">
        <AlertCircle className="h-12 w-12 text-destructive" />
        <div className="text-center">
          <p className="font-semibold">Failed to load messages</p>
          <p className="text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b bg-background">
        <Avatar className="h-10 w-10">
          <AvatarImage
            src={
              getProfilePictureUrl(
                otherUserProfile?.profile_picture_url,
                otherUserProfile?.profile_picture_updated_at
              ) || undefined
            }
            alt={otherUserName}
            loading="lazy"
          />
          <AvatarFallback>{otherUserName[0]?.toUpperCase()}</AvatarFallback>
        </Avatar>
        <div className="flex-1">
          <h2 className="font-semibold">{otherUserName}</h2>
        </div>
      </div>

      {/* Messages */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {offset > 0 && (
          <div className="flex justify-center">
            <Button variant="outline" size="sm" onClick={loadMoreMessages} disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Loading...
                </>
              ) : (
                "Load earlier messages"
              )}
            </Button>
          </div>
        )}

        {displayMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
            <p>No messages yet</p>
            <p className="text-sm">Send a message to start the conversation</p>
          </div>
        ) : (
          displayMessages.map((message) => {
            const isOwnMessage = message.sender_id === user?.id;
            const messageDate = new Date(message.created_at);
            const timeString = messageDate.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            });

            return (
              <div
                key={message.id}
                className={cn("flex gap-2", isOwnMessage ? "justify-end" : "justify-start")}
              >
                {!isOwnMessage && (
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarImage
                      src={
                        getProfilePictureUrl(
                          otherUserProfile?.profile_picture_url,
                          otherUserProfile?.profile_picture_updated_at
                        ) || undefined
                      }
                      alt={otherUserName}
                      loading="lazy"
                    />
                    <AvatarFallback>{otherUserName[0]?.toUpperCase()}</AvatarFallback>
                  </Avatar>
                )}

                <div
                  className={cn(
                    "flex flex-col max-w-[70%]",
                    isOwnMessage ? "items-end" : "items-start"
                  )}
                >
                  <div
                    className={cn(
                      "rounded-lg px-4 py-2 break-words",
                      isOwnMessage ? "bg-primary text-primary-foreground" : "bg-muted"
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <span className="text-xs text-muted-foreground mt-1">{timeString}</span>
                </div>

                {isOwnMessage && (
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarImage
                      src={
                        getProfilePictureUrl(
                          currentUserProfile?.profile_picture_url,
                          currentUserProfile?.profile_picture_updated_at
                        ) || undefined
                      }
                      alt="You"
                      loading="lazy"
                    />
                    <AvatarFallback>{user.username?.[0]?.toUpperCase()}</AvatarFallback>
                  </Avatar>
                )}
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={!isConnected}
        placeholder={isConnected ? "Type a message..." : "Connecting..."}
      />
    </div>
  );
}
