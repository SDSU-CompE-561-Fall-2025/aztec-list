/**
 * TanStack Query options for messaging
 */

import { queryOptions } from "@tanstack/react-query";
import { getConversations, getMessages } from "@/lib/messaging-api";
import { getStoredUser } from "@/lib/auth";

export function createConversationsQueryOptions() {
  const user = getStoredUser();
  return queryOptions({
    queryKey: ["conversations", user?.id], // Include user ID to prevent cache sharing
    queryFn: getConversations,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1,
    enabled: !!user?.id, // Only fetch if user is authenticated
  });
}

export function createMessagesQueryOptions(
  conversationId: string,
  limit: number = 50,
  offset: number = 0
) {
  const user = getStoredUser();
  return queryOptions({
    queryKey: ["messages", conversationId, user?.id, limit, offset], // Include user ID
    queryFn: () => getMessages(conversationId, limit, offset),
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: 1,
    enabled: !!conversationId && !!user?.id, // Ensure user is authenticated
  });
}
