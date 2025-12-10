/**
 * Message and Conversation types matching backend schemas
 */

export interface Conversation {
  id: string;
  user_1_id: string;
  user_2_id: string;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  created_at: string;
}

export interface ConversationCreate {
  other_user_id: string;
}

export interface MessageCreate {
  content: string;
}

export interface ConversationPublic extends Conversation {
  // Extended with computed properties on frontend
  other_user_id?: string;
  last_message?: string;
  last_message_at?: string;
  unread_count?: number;
}

export interface MessagePublic extends Message {}
