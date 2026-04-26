import { Send } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
}

export function ChatInput({ value, onChange, onSend, disabled }: Props) {
  return (
    <div className="flex gap-2 items-end p-4 border-t border-gray-800 bg-gray-950">
      <textarea
        className="flex-1 resize-none rounded-xl bg-gray-800 border border-gray-700 px-4 py-3 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition min-h-[48px] max-h-40"
        placeholder="Message Aria…"
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        rows={1}
      />
      <button
        onClick={onSend}
        disabled={disabled || !value.trim()}
        className={clsx(
          "shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition",
          disabled || !value.trim()
            ? "bg-gray-700 text-gray-500 cursor-not-allowed"
            : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg"
        )}
      >
        <Send size={18} />
      </button>
    </div>
  );
}
