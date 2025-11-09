"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const X = dynamic(() => import("lucide-react").then(m => m.X), { ssr: false });
const Send = dynamic(() => import("lucide-react").then(m => m.Send), { ssr: false });

interface CortexDrawerProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  callCortex: (prompt: string) => Promise<any>;
}

export default function CortexDrawer({ isOpen, onOpenChange, callCortex }: CortexDrawerProps) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: any }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const prompt = input.trim();
    setMessages(m => [...m, { role: "user", content: prompt }]);
    setInput("");
    setLoading(true);

    try {
      const result = await callCortex(prompt);
      setMessages(m => [...m, { role: "assistant", content: result }]);
    } catch {
      setMessages(m => [...m, { role: "assistant", content: "⚠️ Error getting Cortex response." }]);
    } finally {
      setLoading(false);
    }
  };

  const renderAssistantMessage = (content: any) => {
    try {
      // if backend returns JSON string, parse it
      const parsed = typeof content === "string" ? JSON.parse(content) : content;

      if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === "object") {
        const keys = Object.keys(parsed[0]);
        return (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm border border-gray-200 rounded-lg">
              <thead className="bg-gray-100 text-gray-700">
                <tr>
                  {keys.map(k => (
                    <th key={k} className="px-3 py-2 text-left border-b border-gray-200 capitalize">
                      {k.replace(/_/g, " ")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {parsed.map((row, i) => (
                  <tr key={i} className="odd:bg-white even:bg-gray-50">
                    {keys.map(k => (
                      <td key={k} className="px-3 py-2 border-b border-gray-100">
                        {row[k]?.toString() ?? ""}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      }

      // fallback: plain text / stringified
      return <pre className="whitespace-pre-wrap">{JSON.stringify(parsed, null, 2)}</pre>;
    } catch {
      return <div>{content}</div>;
    }
  };

  return (
    <div
      className={`fixed bottom-4 right-0 w-full sm:w-[400px] h-[60%] bg-white shadow-2xl border-t border-l border-gray-200 rounded-t-3xl transform transition-transform duration-300 z-[1200] ${
        isOpen ? "translate-y-0" : "translate-y-full"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-gray-50 rounded-t-3xl">
        <h3 className="font-semibold text-gray-800">🧠 Ask Cortex</h3>
        <button onClick={() => onOpenChange(false)} className="text-gray-400 hover:text-gray-600">
          <X size={20} />
        </button>
      </div>

      {/* Chat history */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 h-[calc(100%-100px)]">
        {messages.length === 0 && (
          <div className="text-sm text-gray-500 italic text-center mt-10">
            Type a question about pothole data, e.g. “Which borough has the most severe potholes?”
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`p-3 rounded-2xl max-w-[85%] ${
              m.role === "user"
                ? "bg-[#FFEDD5] text-gray-800 self-end ml-auto"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            {m.role === "assistant" ? renderAssistantMessage(m.content) : m.content}
          </div>
        ))}
        {loading && <div className="text-sm text-gray-400 italic">Thinking...</div>}
      </div>

      {/* Input */}
      <div className="flex items-center gap-2 p-4 border-t border-gray-200 bg-white">
        <input
          type="text"
          placeholder="Ask about NYC potholes..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="flex-1 px-4 py-2 text-sm border rounded-full focus:outline-none focus:ring-2 focus:ring-[#FF6B6B]"
        />
        <button
          onClick={handleSend}
          disabled={loading}
          className="p-2 rounded-full bg-[#FF6B6B] hover:bg-[#ff8585] text-white transition"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
