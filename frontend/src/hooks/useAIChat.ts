"use client";

import { useCallback, useRef, useState } from "react";
import { type AISource, streamAIChat } from "@/lib/ai-api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: AISource[];
}

function updateLastAssistant(
  messages: ChatMessage[],
  update: (message: ChatMessage) => ChatMessage,
): ChatMessage[] {
  const index = messages.length - 1;
  if (index < 0 || messages[index].role !== "assistant") return messages;
  const next = messages.slice();
  next[index] = update(next[index]);
  return next;
}

/**
 * Manages a single in-session assistant chat: appends the user turn, streams the
 * assistant reply token-by-token, and tracks the server conversation id for
 * multi-turn context.
 */
export function useAIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const conversationId = useRef<string | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      const content = text.trim();
      if (!content || isStreaming) return;

      setError(null);
      setMessages((prev) => [
        ...prev,
        { role: "user", content },
        { role: "assistant", content: "" },
      ]);
      setIsStreaming(true);

      try {
        await streamAIChat(
          { message: content, conversationId: conversationId.current },
          (event) => {
            if (event.type === "start") {
              conversationId.current = event.conversation_id;
            } else if (event.type === "sources") {
              setMessages((prev) =>
                updateLastAssistant(prev, (m) => ({ ...m, sources: event.sources })),
              );
            } else if (event.type === "token") {
              setMessages((prev) =>
                updateLastAssistant(prev, (m) => ({ ...m, content: m.content + event.content })),
              );
            } else if (event.type === "error") {
              setError(event.message);
            }
          },
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Something went wrong");
      } finally {
        setIsStreaming(false);
      }
    },
    [isStreaming],
  );

  return { messages, isStreaming, error, sendMessage };
}
