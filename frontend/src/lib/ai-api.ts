import { getAuthToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/constants";

export interface AISource {
  id: string;
  title: string;
}

export type AIChatEvent =
  | { type: "start"; conversation_id: string }
  | { type: "sources"; sources: AISource[] }
  | { type: "token"; content: string }
  | { type: "done"; message_id: string }
  | { type: "error"; message: string };

interface StreamParams {
  message: string;
  conversationId?: string | null;
}

/**
 * POST a message to the AI assistant and stream its Server-Sent Events,
 * invoking `onEvent` for each parsed event (start, sources, token, done, error).
 */
export const streamAIChat = async (
  params: StreamParams,
  onEvent: (event: AIChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error("Authentication required");
  }

  const res = await fetch(`${API_BASE_URL}/ai/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      message: params.message,
      conversation_id: params.conversationId ?? undefined,
    }),
    signal,
  });

  if (!res.ok || !res.body) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Assistant request failed: ${res.status} ${detail}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result = await reader.read();

  while (!result.done) {
    buffer += decoder.decode(result.value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const json = line.slice(line.indexOf(":") + 1).trim();
      if (!json) continue;
      try {
        onEvent(JSON.parse(json) as AIChatEvent);
      } catch {
        // Ignore malformed chunk.
      }
    }

    result = await reader.read();
  }
};
