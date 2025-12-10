/**
 * WebSocket hook for real-time messaging
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { getAuthToken } from "@/lib/auth";
import { Message } from "@/types/message";

// Determine WebSocket URL based on API URL
function getWebSocketUrl(conversationId: string, token: string): string {
  // Get the base URL without /api/v1 if present
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  const baseUrl = apiBaseUrl.replace(/\/api\/v1$/, "");

  // Convert HTTP(S) URL to WS(S)
  const wsUrl = baseUrl.replace(/^http/, "ws");

  return `${wsUrl}/api/v1/messages/ws/conversations/${conversationId}?token=${token}`;
}

interface UseWebSocketOptions {
  conversationId: string;
  onMessage: (message: Message) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
}

export function useWebSocket({
  conversationId,
  onMessage,
  onError,
  onConnect,
  onDisconnect,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const maxReconnectAttempts = 10; // Increased for better reliability
  const baseReconnectDelay = 2000; // Slightly faster initial retry
  const hasShownMaxRetriesError = useRef(false);

  // Use a ref to store the connect function to avoid hoisting issues
  const connectFnRef = useRef<(() => void) | undefined>(undefined);

  const connect = useCallback(() => {
    const token = getAuthToken();
    if (!token) {
      console.error("No auth token available for WebSocket connection");
      return;
    }

    // Don't create multiple connections
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING
    ) {
      return;
    }

    setIsConnecting(true);

    try {
      const url = getWebSocketUrl(conversationId, token);
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log(`WebSocket connected to conversation ${conversationId}`);
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0; // Reset reconnect counter on successful connection
        hasShownMaxRetriesError.current = false; // Reset error flag
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: Message = JSON.parse(event.data);
          onMessage(message);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setIsConnecting(false);
        onError?.(error);
      };

      ws.onclose = (event) => {
        console.log(`WebSocket disconnected: ${event.code} ${event.reason}`);
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        // Auto-reconnect with exponential backoff if not a normal closure
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            baseReconnectDelay * Math.pow(1.5, reconnectAttemptsRef.current),
            30000 // Cap at 30 seconds
          );
          reconnectAttemptsRef.current += 1;

          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Attempting to reconnect... (attempt ${reconnectAttemptsRef.current})`);
            connectFnRef.current?.();
          }, delay);
        } else if (
          reconnectAttemptsRef.current >= maxReconnectAttempts &&
          !hasShownMaxRetriesError.current
        ) {
          console.error("Max reconnection attempts reached");
          hasShownMaxRetriesError.current = true;
          onError?.(new Event("Max reconnection attempts reached"));
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Failed to create WebSocket connection:", error);
      setIsConnecting(false);
    }
  }, [conversationId, onMessage, onError, onConnect, onDisconnect]);

  // Store connect function in ref (inside effect to avoid render-phase assignment)
  useEffect(() => {
    connectFnRef.current = connect;
  }, [connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close(1000, "Client disconnect");
      wsRef.current = null;
    }

    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }

    const messageData = { content };
    wsRef.current.send(JSON.stringify(messageData));
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      hasShownMaxRetriesError.current = false;
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    sendMessage,
    reconnect: connect,
    disconnect,
  };
}
