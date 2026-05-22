/**
 * Unit tests for the useAIChat hook (assistant chat state + streaming wiring).
 */

import { act, renderHook } from "@testing-library/react";
import { streamAIChat } from "@/lib/ai-api";
import { useAIChat } from "../useAIChat";

jest.mock("@/lib/ai-api", () => ({
  streamAIChat: jest.fn(),
}));

const mockStream = streamAIChat as jest.Mock;

describe("useAIChat", () => {
  beforeEach(() => {
    mockStream.mockReset();
  });

  it("appends the user turn and streams the assistant reply with sources", async () => {
    mockStream.mockImplementation(async (_params, onEvent) => {
      onEvent({ type: "start", conversation_id: "c1" });
      onEvent({ type: "sources", sources: [{ id: "l1", title: "Wooden desk" }] });
      onEvent({ type: "token", content: "A " });
      onEvent({ type: "token", content: "desk." });
      onEvent({ type: "done", message_id: "m1" });
    });

    const { result } = renderHook(() => useAIChat());
    await act(async () => {
      await result.current.sendMessage("find a desk");
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0]).toMatchObject({ role: "user", content: "find a desk" });

    const assistant = result.current.messages[1];
    expect(assistant.role).toBe("assistant");
    expect(assistant.content).toBe("A desk.");
    expect(assistant.sources).toEqual([{ id: "l1", title: "Wooden desk" }]);
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("reuses the conversation id on the next turn", async () => {
    mockStream.mockImplementation(async (_params, onEvent) => {
      onEvent({ type: "start", conversation_id: "conv-1" });
      onEvent({ type: "token", content: "ok" });
      onEvent({ type: "done", message_id: "m" });
    });

    const { result } = renderHook(() => useAIChat());
    await act(async () => {
      await result.current.sendMessage("hi");
    });
    await act(async () => {
      await result.current.sendMessage("more");
    });

    expect(mockStream).toHaveBeenLastCalledWith(
      expect.objectContaining({ message: "more", conversationId: "conv-1" }),
      expect.any(Function),
    );
  });

  it("surfaces a streamed error event", async () => {
    mockStream.mockImplementation(async (_params, onEvent) => {
      onEvent({ type: "error", message: "boom" });
    });

    const { result } = renderHook(() => useAIChat());
    await act(async () => {
      await result.current.sendMessage("hi");
    });

    expect(result.current.error).toBe("boom");
    expect(result.current.isStreaming).toBe(false);
  });
});
