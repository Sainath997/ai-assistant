import { useState, useRef, useEffect, useCallback } from "react";

export type Role = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: Role;
  content: string;
  thinking?: boolean;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hi! I'm **Aria**, your personal AI assistant. I can search the web, read and write files, run code, remember things, and manage your calendar. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const token = localStorage.getItem("apiToken") || "";
    const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : "";
    const ws = new WebSocket(`${protocol}://${window.location.host}/api/ws/chat${tokenQuery}`);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      setTimeout(connect, 2000);
    };
    ws.onerror = () => ws.close();

    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data);
      if (data.type === "thinking") {
        setIsThinking(true);
      } else if (data.type === "message") {
        setIsThinking(false);
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== "thinking"),
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: data.content,
          },
        ]);
      }
    };

    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: text },
    ]);
    setInput("");
    wsRef.current.send(JSON.stringify({ message: text }));
  }, [input]);

  const clearHistory = useCallback(async () => {
    await fetch("/api/chat/ws_default", { method: "DELETE" });
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "Chat cleared! How can I help you?",
      },
    ]);
  }, []);

  return { messages, input, setInput, sendMessage, clearHistory, isConnected, isThinking };
}
