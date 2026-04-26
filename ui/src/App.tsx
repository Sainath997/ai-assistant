import { useEffect, useRef } from "react";
import { Trash2, Wifi, WifiOff } from "lucide-react";
import { useChat } from "./hooks/useChat";
import { ChatMessage } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";

export default function App() {
  const { messages, input, setInput, sendMessage, clearHistory, isConnected, isThinking } =
    useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-4 border-b border-gray-800 bg-gray-950/80 backdrop-blur sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center font-bold shadow-lg">
            A
          </div>
          <div>
            <h1 className="font-semibold text-gray-100">Aria</h1>
            <p className="text-xs text-gray-500">Agentic AI Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs text-gray-500">
            {isConnected ? (
              <><Wifi size={13} className="text-green-400" /> Live</>
            ) : (
              <><WifiOff size={13} className="text-red-400" /> Reconnecting…</>
            )}
          </span>
          <button
            onClick={clearHistory}
            title="Clear chat"
            className="p-2 rounded-lg hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto py-4 space-y-1">
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
        {isThinking && (
          <ChatMessage
            message={{ id: "thinking", role: "assistant", content: "", thinking: true }}
          />
        )}
        <div ref={bottomRef} />
      </main>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={setInput}
        onSend={sendMessage}
        disabled={!isConnected || isThinking}
      />
    </div>
  );
}
