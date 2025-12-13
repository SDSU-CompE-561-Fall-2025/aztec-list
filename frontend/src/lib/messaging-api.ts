/**
 * Messaging API client functions
 */

import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import { Conversation, Message, ConversationCreate } from "@/types/message";

/**
 * Get all conversations for the authenticated user
 */
export async function getConversations(): Promise<Conversation[]> {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${API_BASE_URL}/messages/conversations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("SESSION_EXPIRED");
    }
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch conversations: ${response.status} ${errorText}`);
  }

  return response.json();
}

/**
 * Create a new conversation or get existing one
 */
export async function createOrGetConversation(otherUserId: string): Promise<Conversation> {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const body: ConversationCreate = {
    other_user_id: otherUserId,
  };

  const response = await fetch(`${API_BASE_URL}/messages/conversations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let errorDetail = "Unknown error";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || JSON.stringify(errorData);
    } catch {
      errorDetail = await response.text().catch(() => "Unknown error");
    }

    // If unauthorized, throw a specific error for token expiration
    if (response.status === 401) {
      throw new Error("SESSION_EXPIRED");
    }

    throw new Error(`Failed to create conversation: ${response.status} - ${errorDetail}`);
  }

  return response.json();
}

/**
 * Get messages for a specific conversation with pagination
 */
export async function getMessages(
  conversationId: string,
  limit: number = 20,
  offset: number = 0
): Promise<Message[]> {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const url = new URL(`${API_BASE_URL}/messages/conversations/${conversationId}/messages`);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("SESSION_EXPIRED");
    }
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Failed to fetch messages: ${response.status} ${errorText}`);
  }

  return response.json();
}
