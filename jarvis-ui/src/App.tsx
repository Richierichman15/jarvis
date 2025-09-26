import { useEffect, useMemo, useState } from "react";
import { listTools, runNL } from "./api";
import { startSTT, speak } from "./voice";
import "./App.css";

type Tool = { name: string; description?: string };
type Message = { role: "user" | "assistant"; text: string; meta?: Record<string, any> };

export default function App() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [filter, setFilter] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const data = await listTools();
        const list = Array.isArray(data) ? data : data?.tools ?? [];
        setTools(list);
      } catch (e) {
        console.error("Failed to load tools", e);
      }
    })();
  }, []);

  const filteredTools = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return tools;
    return tools.filter((t) => t.name.toLowerCase().includes(q));
  }, [filter, tools]);

  async function sendMessage(message?: string) {
    const text = (message ?? input).trim();
    if (!text || isSending) return;
    setIsSending(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);

    try {
      const response = await runNL(text);
      const assistantText = response?.text ? String(response.text) : "(no response)";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: assistantText,
          meta: response?.meta,
        },
      ]);
      if (assistantText) speak(assistantText.slice(0, 400), { debug: true });
    } catch (err: any) {
      console.error("/nl failed", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Sorry, that failed: ${err?.message || err}` },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  function handleToolClick(tool: Tool) {
    const hint = `Use ${tool.name} to ${tool.description || "..."}`;
    setInput((prev) => (prev ? `${prev} ${hint}` : hint));
  }

  function handleMic() {
    startSTT((t) => setInput(t), { debug: true });
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendMessage();
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <h2>Tools</h2>
        <input
          className="tool-search"
          placeholder="Search tools"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
        <div className="tool-list">
          {filteredTools.map((tool) => (
            <button key={tool.name} className="tool-item" onClick={() => handleToolClick(tool)}>
              <span className="tool-name">{tool.name}</span>
              {tool.description && <span className="tool-desc">{tool.description}</span>}
            </button>
          ))}
          {!filteredTools.length && <p className="tool-empty">No tools match.</p>}
        </div>
      </aside>

      <main className="chat">
        <header className="chat-header">Jarvis Console</header>
        <section className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="bubble">{msg.text}</div>
              {msg.meta?.routed_tool && (
                <div className="meta-badge">via {msg.meta.routed_tool}</div>
              )}
            </div>
          ))}
          {!messages.length && (
            <div className="message message-assistant">
              <div className="bubble">Hi! Ask me anything or pick a tool from the left.</div>
            </div>
          )}
        </section>

        <form className="chat-input" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isSending}
          />
          <button type="button" onClick={handleMic} disabled={isSending}>
            🎤
          </button>
          <button type="submit" disabled={isSending}>Send</button>
        </form>
      </main>
    </div>
  );
}
