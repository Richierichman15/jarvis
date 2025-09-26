import { useEffect, useMemo, useState } from "react";
import { listTools, runTool, runPlan } from "./api";
import { startSTT, speak } from "./voice";
import "./App.css";

type Tool = { name: string; description?: string; inputSchema?: any };

function pretty(x: any) {
  try {
    return JSON.stringify(x, null, 2);
  } catch (err) {
    console.error("Failed to pretty print", err, x);
    return String(x);
  }
}

function extractText(out: any): string | null {
  try {
    if (!out) return null;
    if (typeof out === "string") return out;
    if (Array.isArray(out)) return null;
    const content = out.content ?? out.result?.content ?? null;
    if (Array.isArray(content)) {
      const t = content.find((c: any) => c?.text)?.text;
      if (t) return String(t);
    }
    const results = out.results ?? null;
    if (Array.isArray(results) && results[0]?.data) {
      return String(results.map((r: any) => r.data).join("\n")).slice(0, 500);
    }
    return null;
  } catch (err) {
    console.error("Failed to extract text", err, out);
    return null;
  }
}

export default function App() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [argsJson, setArgsJson] = useState<string>("{}");
  const [result, setResult] = useState<any>(null);

  const [planJson, setPlanJson] = useState<string>(
    JSON.stringify(
      {
        steps: [
          { server: "budget", tool: "budget.get_balance", args: {} },
          { server: "trading", tool: "trading.get_price", args: { symbol: "BTC/USDT" } },
        ],
      },
      null,
      2,
    ),
  );
  const [planResult, setPlanResult] = useState<any>(null);

  const [chatInput, setChatInput] = useState<string>("hi jarvis, what can you do?");
  const selectedTool = useMemo(() => tools.find((t) => t.name === selected), [tools, selected]);

  useEffect(() => {
    (async () => {
      try {
        const data = await listTools();
        const list = Array.isArray(data) ? data : data?.tools ?? [];
        setTools(list);
        if (list.length) setSelected(list[0].name);
      } catch (e) {
        console.error("Failed to load tools", e);
      }
    })();
  }, []);

  async function onRunTool() {
    try {
      const args = argsJson.trim() ? JSON.parse(argsJson) : {};
      const out = await runTool(selected, args);
      setResult(out);
      const text = extractText(out);
      if (selected === "jarvis_chat" && text) speak(text.slice(0, 400), { debug: true });
    } catch (e: any) {
      console.error("Run tool failed", e);
      setResult({ error: String(e.message || e) });
    }
  }

  async function onRunPlan() {
    try {
      const body = JSON.parse(planJson);
      const steps = body.steps ?? body;
      const out = await runPlan(steps);
      setPlanResult(out);
      const text = extractText(out);
      if (text) speak(text.slice(0, 400), { debug: true });
    } catch (e: any) {
      console.error("Run plan failed", e);
      setPlanResult({ error: String(e.message || e) });
    }
  }

  function onMic() {
    startSTT((t) => setChatInput(t), { debug: true });
  }

  async function sendChat() {
    setSelected("jarvis_chat");
    setArgsJson(JSON.stringify({ message: chatInput }, null, 2));
    await onRunTool();
  }

  const combinedResult = result ?? planResult;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, padding: 16 }}>
      <section style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <h2>Run Tool</h2>
        <div>
          <label>Tool&nbsp;</label>
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            {tools.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
        </div>
        <small>{selectedTool?.description}</small>
        <h4>Args (JSON)</h4>
        <textarea
          value={argsJson}
          onChange={(e) => setArgsJson(e.target.value)}
          rows={12}
          style={{ width: "100%", fontFamily: "monospace" }}
        />
        <button onClick={onRunTool}>Run Tool</button>

        <hr />
        <h3>Chat</h3>
        <div style={{ display: "flex", gap: 8 }}>
          <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} style={{ flex: 1 }} />
          <button onClick={onMic}>🎤</button>
          <button onClick={sendChat}>Send</button>
        </div>
      </section>

      <section style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <h2>Run Plan (multi-server)</h2>
        <textarea
          value={planJson}
          onChange={(e) => setPlanJson(e.target.value)}
          rows={20}
          style={{ width: "100%", fontFamily: "monospace" }}
        />
        <button onClick={onRunPlan}>Run Plan</button>
      </section>

      <section style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <h2>Result</h2>
        <pre
          style={{
            background: "#111",
            color: "#0f0",
            padding: 12,
            borderRadius: 8,
            overflow: "auto",
            maxHeight: "80vh",
          }}
        >
          {pretty(combinedResult)}
        </pre>
      </section>
    </div>
  );
}
