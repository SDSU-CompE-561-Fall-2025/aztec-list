/**
 * Messaging API client functions
 */

import { API_BASE_URL } from "@/lib/constants";
import { getAuthToken } from "@/lib/auth";
import { Conversation, Message, ConversationCreate } from "@/types/message";

/** Reasons a user can pick when reporting a message. Matches the backend enum. */
export const MESSAGE_REPORT_CATEGORIES = [
  { value: "spam", label: "Spam" },
  { value: "harassment", label: "Harassment" },
  { value: "scam", label: "Scam or fraud" },
  { value: "hate", label: "Hate speech" },
  { value: "nudity", label: "Nudity or sexual content" },
  { value: "other", label: "Something else" },
] as const;

export type MessageReportCategory = (typeof MESSAGE_REPORT_CATEGORIES)[number]["value"];

export interface BlockedUser {
  blocked_user_id: string;
  blocked_username: string | null;
  created_at: string;
}

interface BlockedUserListResponse {
  items: BlockedUser[];
  count: number;
}

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
    let errorDetail: string;
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
  offset: number = 0,
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

/** Read the auth token or throw the standard "not signed in" error. */
function requireToken(): string {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }
  return token;
}

/** Pull a human-readable `detail` (or status text) out of a failed response. */
async function errorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const data = await response.json();
    return data.detail || JSON.stringify(data);
  } catch {
    return response.text().catch(() => fallback);
  }
}

/**
 * Report a message for moderator review.
 */
export async function reportMessage(
  messageId: string,
  category: MessageReportCategory,
  reasonText?: string,
): Promise<void> {
  const token = requireToken();

  const response = await fetch(`${API_BASE_URL}/messages/${messageId}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ category, reason_text: reasonText || null }),
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error("SESSION_EXPIRED");
    throw new Error(await errorDetail(response, "Failed to report message"));
  }
}

/**
 * Block another user (idempotent). The blocked user can no longer start a new
 * conversation with, or send new messages to, the current user.
 */
export async function blockUser(userId: string): Promise<void> {
  const token = requireToken();

  const response = await fetch(`${API_BASE_URL}/users/${userId}/block`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error("SESSION_EXPIRED");
    throw new Error(await errorDetail(response, "Failed to block user"));
  }
}

/**
 * Unblock a user (idempotent).
 */
export async function unblockUser(userId: string): Promise<void> {
  const token = requireToken();

  const response = await fetch(`${API_BASE_URL}/users/${userId}/block`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error("SESSION_EXPIRED");
    throw new Error(await errorDetail(response, "Failed to unblock user"));
  }
}

/**
 * List the users the current user has blocked.
 */
export async function listMyBlocks(): Promise<BlockedUser[]> {
  const token = requireToken();

  const response = await fetch(`${API_BASE_URL}/users/me/blocks`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    if (response.status === 401) throw new Error("SESSION_EXPIRED");
    throw new Error(await errorDetail(response, "Failed to load blocked users"));
  }

  const data: BlockedUserListResponse = await response.json();
  return data.items;
}
