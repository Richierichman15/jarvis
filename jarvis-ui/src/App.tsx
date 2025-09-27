import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { listTools, runNL, listServers, connectServer, disconnectServer } from "./api";
import { startSTT, startContinuousSTT, stopContinuousSTT, speak } from "./voice";
import "./App.css";

type Tool = { name: string; description?: string };
type MessageMeta = {
  routed_tool?: string;
  server?: string;
  data?: unknown;
};
type Message = {
  role: "user" | "assistant";
  text: string;
  meta?: MessageMeta;
};

type ServerInfo = {
  alias: string;
  connected: boolean;
  default?: boolean;
  saved?: boolean;
  command?: string | null;
  args?: string[];
  cwd?: string | null;
  env?: Record<string, string> | null;
  status?: string;
};

export default function App() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [filter, setFilter] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [serversLoading, setServersLoading] = useState(false);
  const [serverBusy, setServerBusy] = useState<string | null>(null);
  const [serverMessage, setServerMessage] = useState<string | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [newAlias, setNewAlias] = useState("");
  const [newCommand, setNewCommand] = useState("");
  const [newArgs, setNewArgs] = useState("");

  const voiceHandleRef = useRef<{ stop: () => void } | null>(null);
  const voiceQueueRef = useRef<string[]>([]);
  const lastVoiceRef = useRef<string>("");
  const isSendingRef = useRef(false);
  const inputRef = useRef("");

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

  useEffect(() => {
    isSendingRef.current = isSending;
  }, [isSending]);

  useEffect(() => {
    inputRef.current = input;
  }, [input]);

  const filteredTools = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return tools;
    return tools.filter((t) => t.name.toLowerCase().includes(q));
  }, [filter, tools]);

  const refreshServers = useCallback(async () => {
    setServersLoading(true);
    try {
      const data = await listServers();
      const list = Array.isArray(data?.servers)
        ? (data.servers as ServerInfo[]).map((entry) => ({
            ...entry,
            args: Array.isArray(entry.args) ? entry.args : [],
          }))
        : [];
      setServers(list);
    } catch (err) {
      console.error("Failed to load servers", err);
      setServerError(extractErrorMessage(err));
    } finally {
      setServersLoading(false);
    }
  }, []);

  const orderedServers = useMemo(() => {
    const list = [...servers];
    list.sort((a, b) => {
      if (a.connected !== b.connected) {
        return a.connected ? -1 : 1;
      }
      if ((a.default ?? false) !== (b.default ?? false)) {
        return a.default ? -1 : 1;
      }
      return a.alias.localeCompare(b.alias);
    });
    return list;
  }, [servers]);

  useEffect(() => {
    void refreshServers();
  }, [refreshServers]);

  useEffect(() => {
    if (!serverMessage && !serverError) return;
    const timer = window.setTimeout(() => {
      setServerMessage(null);
      setServerError(null);
    }, 4000);
    return () => window.clearTimeout(timer);
  }, [serverMessage, serverError]);

  const sendMessage = useCallback(
    async (message?: string, options: { fromVoice?: boolean } = {}) => {
      const { fromVoice = false } = options;
      const raw = message ?? inputRef.current;
      const text = raw.trim();
      if (!text || isSendingRef.current) {
        if (!fromVoice) {
          setInput("");
          inputRef.current = "";
        }
        return;
      }

      isSendingRef.current = true;
      setIsSending(true);
      if (!fromVoice) {
        setInput("");
        inputRef.current = "";
      }
      setMessages((prev) => [...prev, { role: "user", text }]);

      try {
        const response = await runNL(text);
        const assistantText = response?.text ? String(response.text) : "(no response)";
        const meta: MessageMeta | undefined = response?.meta;
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: assistantText,
            meta,
          },
        ]);
        if (assistantText) speak(assistantText.slice(0, 400), { debug: true });
      } catch (rawErr) {
        const err = rawErr as Error;
        console.error("/nl failed", err);
        const messageError = err?.message ?? String(rawErr ?? "Unknown error");
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: `Sorry, that failed: ${messageError}` },
        ]);
      } finally {
        isSendingRef.current = false;
        setIsSending(false);
        if (voiceQueueRef.current.length > 0) {
          const next = voiceQueueRef.current.shift();
          lastVoiceRef.current = "";
          if (next) {
            setTimeout(() => {
              void sendMessage(next, { fromVoice: true });
            }, 0);
          }
        } else {
          lastVoiceRef.current = "";
        }
      }
    },
    []
  );

  const enqueueVoice = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;
      if (trimmed === lastVoiceRef.current) return;
      lastVoiceRef.current = trimmed;
      voiceQueueRef.current.push(trimmed);
      if (!isSendingRef.current) {
        const next = voiceQueueRef.current.shift();
        if (next) {
          void sendMessage(next, { fromVoice: true });
        }
      }
    },
    [sendMessage]
  );

  useEffect(() => {
    if (!voiceEnabled) {
      voiceHandleRef.current?.stop?.();
      voiceHandleRef.current = null;
      stopContinuousSTT();
      voiceQueueRef.current = [];
      lastVoiceRef.current = "";
      setIsRecording(false);
      return;
    }

    voiceQueueRef.current = [];
    lastVoiceRef.current = "";
    setIsRecording(false);

    const handle = startContinuousSTT({
      onText: enqueueVoice,
      onStatus: (status) => {
        if (status === "start") {
          setIsRecording(true);
        } else {
          setIsRecording(false);
        }
      },
      debug: true,
    });

    voiceHandleRef.current = handle;

    return () => {
      handle.stop();
      voiceHandleRef.current = null;
      setIsRecording(false);
    };
  }, [voiceEnabled, enqueueVoice]);

  const toggleVoiceMode = () => {
    setVoiceEnabled((prev) => !prev);
  };

  const cancelVoiceMode = () => {
    voiceQueueRef.current = [];
    lastVoiceRef.current = "";
    voiceHandleRef.current?.stop?.();
    stopContinuousSTT();
    setVoiceEnabled(false);
  };

  const handleServerConnect = useCallback(
    async (info: ServerInfo) => {
      const command = (info.command ?? "").trim();
      if (!command) {
        setServerError(`No launch command saved for '${info.alias}'.`);
        return;
      }
      setServerBusy(info.alias);
      setServerError(null);
      setServerMessage(null);
      try {
        await connectServer({
          alias: info.alias,
          command,
          args: info.args ?? [],
          save: info.saved ?? true,
          cwd: info.cwd ?? undefined,
          env: info.env ?? undefined,
        });
        setServerMessage(`Connected '${info.alias}'.`);
        await refreshServers();
      } catch (err) {
        setServerError(extractErrorMessage(err));
      } finally {
        setServerBusy(null);
      }
    },
    [refreshServers]
  );

  const handleServerDisconnect = useCallback(
    async (info: ServerInfo, forget = false) => {
      if (info.default) {
        setServerError("Cannot disconnect the default Jarvis server.");
        return;
      }
      setServerBusy(info.alias);
      setServerError(null);
      setServerMessage(null);
      try {
        await disconnectServer(info.alias, { forget });
        setServerMessage(forget ? `Removed '${info.alias}'.` : `Disconnected '${info.alias}'.`);
        await refreshServers();
      } catch (err) {
        setServerError(extractErrorMessage(err));
      } finally {
        setServerBusy(null);
      }
    },
    [refreshServers]
  );

  const handleLaunchNew = useCallback(async () => {
    const alias = newAlias.trim();
    const command = newCommand.trim();
    if (!alias || !command) {
      setServerError("Alias and command are required to launch a server.");
      return;
    }
    const args = splitArgs(newArgs.trim());
    setServerBusy("__launch__");
    setServerError(null);
    setServerMessage(null);
    try {
      await connectServer({ alias, command, args, save: true });
      setServerMessage(`Connected '${alias}'.`);
      setNewAlias("");
      setNewCommand("");
      setNewArgs("");
      await refreshServers();
    } catch (err) {
      setServerError(extractErrorMessage(err));
    } finally {
      setServerBusy(null);
    }
  }, [newAlias, newCommand, newArgs, refreshServers]);

  const handleToolClick = (tool: Tool) => {
    const hint = `Use ${tool.name} to ${tool.description || "..."}`;
    setInput((prev) => (prev ? `${prev} ${hint}` : hint));
  };

  const handleMic = () => {
    if (voiceEnabled) {
      return;
    }
    startSTT((t) => setInput(t), { debug: true });
  };

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    void sendMessage();
  }

  return (
    <div className="app-container">
      <aside className="sidebar">
        <section className="panel tools-panel">
          <div className="panel-header">
            <h2>Tools</h2>
          </div>
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
        </section>

        <section className="panel servers-panel">
          <div className="panel-header servers-header">
            <h2>Servers</h2>
            <div className="servers-actions">
              {serversLoading ? (
                <span className="servers-status">Loading…</span>
              ) : (
                <button
                  type="button"
                  className="refresh-btn"
                  onClick={() => void refreshServers()}
                  disabled={serverBusy !== null}
                  title="Refresh servers"
                >
                  ↻
                </button>
              )}
            </div>
          </div>
          {serverMessage && <div className="server-msg success">{serverMessage}</div>}
          {serverError && <div className="server-msg error">{serverError}</div>}
          <div className="server-list">
            {orderedServers.map((srv) => {
              const preview = buildCommandPreview(srv);
              const busy = serverBusy === srv.alias;
              return (
                <div key={srv.alias} className={`server-item ${srv.connected ? "connected" : ""}`}>
                  <div className="server-row">
                    <span className="server-alias">{srv.alias}</span>
                    <div className="server-tags">
                      {srv.default && <span className="server-pill primary">default</span>}
                      {srv.connected && <span className="server-pill online">online</span>}
                      {!srv.connected && srv.saved && <span className="server-pill muted">saved</span>}
                    </div>
                  </div>
                  {preview && <div className="server-command" title={preview}>{preview}</div>}
                  <div className="server-actions">
                    <button
                      type="button"
                      onClick={() => handleServerConnect(srv)}
                      disabled={srv.connected || !srv.command || busy || serverBusy === "__launch__"}
                    >
                      Connect
                    </button>
                    <button
                      type="button"
                      onClick={() => handleServerDisconnect(srv)}
                      disabled={!srv.connected || srv.default || busy}
                    >
                      Disconnect
                    </button>
                    {srv.saved && !srv.default && (
                      <button
                        type="button"
                        className="ghost-btn"
                        onClick={() => handleServerDisconnect(srv, true)}
                        disabled={busy}
                      >
                        Forget
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
            {!orderedServers.length && <p className="tool-empty">No servers registered.</p>}
          </div>
          <div className="server-form">
            <h3>Launch Server</h3>
            <input
              placeholder="Alias (e.g. search)"
              value={newAlias}
              onChange={(e) => setNewAlias(e.target.value)}
            />
            <input
              placeholder="Command (e.g. python3)"
              value={newCommand}
              onChange={(e) => setNewCommand(e.target.value)}
            />
            <input
              placeholder="Args (optional, space separated)"
              value={newArgs}
              onChange={(e) => setNewArgs(e.target.value)}
            />
            <button
              type="button"
              onClick={handleLaunchNew}
              disabled={serverBusy !== null || serversLoading}
            >
              Launch
            </button>
          </div>
        </section>
      </aside>

      <main className="chat">
        <header className="chat-header">
          <span>Jarvis Console</span>
          <div className="voice-controls">
            <span className={`mic-indicator ${isRecording ? "active" : ""}`} />
            <span className="voice-status">
              {voiceEnabled ? (isRecording ? "Listening…" : "Voice Ready") : "Voice Off"}
            </span>
            <button type="button" onClick={toggleVoiceMode}>
              {voiceEnabled ? "Disable Voice" : "Enable Voice"}
            </button>
            {isRecording && (
              <button type="button" className="cancel-btn" onClick={cancelVoiceMode}>
                Cancel
              </button>
            )}
          </div>
        </header>
        <section className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message message-${msg.role}`}>
              <div className="bubble">
                <div className="bubble-text">{msg.text}</div>
                {msg.role === "assistant" && (
                  <ResultCard meta={msg.meta} text={msg.text} />
                )}
              </div>
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
          <button type="button" onClick={handleMic} disabled={isSending || voiceEnabled}>
            🎤
          </button>
          <button type="submit" disabled={isSending}>Send</button>
        </form>
      </main>
    </div>
  );
}

type ResultCardProps = {
  meta?: Message["meta"];
  text: string;
};

function ResultCard({ meta, text }: ResultCardProps) {
  const tool = meta?.routed_tool;
  const server = meta?.server;
  if (!tool) return null;

  let data = meta?.data;
  if (typeof data === "string") {
    data = parseJSON(data) ?? data;
  }
  if (data == null) {
    data = parseJSON(text);
  }

  if (tool === "fitness.list_workouts" && Array.isArray(data)) {
    const workouts = data.filter(isRecord);
    if (!workouts.length) {
      return <div className="meta-badge">via {tool}{server ? ` • ${server}` : ""} — no workouts found.</div>;
    }
    return (
      <div className="result-card">
        <div className="meta-badge">via {tool}{server ? ` • ${server}` : ""}</div>
        <table className="result-table">
          <thead>
            <tr>
              <th>Exercise</th>
              <th>Muscle Group</th>
              <th>Equipment</th>
            </tr>
          </thead>
          <tbody>
            {workouts.slice(0, 10).map((item, idx) => (
              <tr key={idx}>
                <td>{getFirstString(item, ["name", "title"]) ?? "Exercise"}</td>
                <td>{getFirstString(item, ["muscle_group", "muscles"]) ?? "-"}</td>
                <td>{getFirstString(item, ["equipment"]) ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {workouts.length > 10 && <div className="meta-badge">…and {workouts.length - 10} more</div>}
      </div>
    );
  }

  if (tool === "budget.get_balance" && isRecord(data)) {
    return (
      <div className="result-card">
        <div className="meta-badge">via {tool}{server ? ` • ${server}` : ""}</div>
        <div className="balance-card">
          <div>
            <span className="label">Income</span>
            <span className="value">{formatCurrency(data.income)}</span>
          </div>
          <div>
            <span className="label">Expenses</span>
            <span className="value">{formatCurrency(data.expenses)}</span>
          </div>
          <div>
            <span className="label">Balance</span>
            <span className="value focus">{formatCurrency(data.balance)}</span>
          </div>
        </div>
      </div>
    );
  }

  if (tool === "trading.get_price" && isRecord(data)) {
    const change = typeof data.change === "number" ? data.change : Number(data.change);
    return (
      <div className="result-card">
        <div className="meta-badge">via {tool}{server ? ` • ${server}` : ""}</div>
        <div className="ticker-card">
          <div className="ticker-symbol">{typeof data.symbol === "string" ? data.symbol : "Symbol"}</div>
          <div className="ticker-price">{formatCurrencyNumber(data.price)}</div>
          {Number.isFinite(change) && (
            <div className={`ticker-change ${change >= 0 ? "pos" : "neg"}`}>
              {change.toFixed(2)}%
            </div>
          )}
        </div>
      </div>
    );
  }

  if (tool && server) {
    return <div className="meta-badge">via {tool} • {server}</div>;
  }
  if (tool) {
    return <div className="meta-badge">via {tool}</div>;
  }
  return null;
}

function buildCommandPreview(info: Pick<ServerInfo, "command" | "args">): string {
  const parts: string[] = [];
  if (info.command) parts.push(info.command);
  if (Array.isArray(info.args)) {
    for (const arg of info.args) {
      if (typeof arg === "string" && arg.length) {
        parts.push(arg);
      }
    }
  }
  return parts.join(" ").trim();
}

function splitArgs(input: string): string[] {
  if (!input) return [];
  const matches = input.match(/(?:[^\s"']+|"[^"]*"|'[^']*')+/g);
  if (!matches) return [];
  return matches.map((token) => token.replace(/^['"]|['"]$/g, ""));
}

function extractErrorMessage(err: unknown): string {
  if (!err) return "Unknown error";
  if (typeof err === "string") return err;
  const maybeResponse = (err as { response?: { data?: any } }).response;
  if (maybeResponse?.data) {
    const detail = maybeResponse.data.detail ?? maybeResponse.data.error ?? maybeResponse.data.message;
    if (detail) return String(detail);
  }
  if (err instanceof Error && err.message) return err.message;
  try {
    return JSON.stringify(err);
  } catch {
    return String(err);
  }
}

function parseJSON(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getFirstString(record: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    const val = record[key];
    if (typeof val === "string") return val;
  }
  return undefined;
}

function formatCurrency(value: unknown): string {
  const num = typeof value === "number" ? value : Number(value ?? NaN);
  if (Number.isNaN(num)) return String(value ?? "-");
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num);
}

function formatCurrencyNumber(value: unknown): string {
  const num = typeof value === "number" ? value : Number(value ?? NaN);
  if (Number.isNaN(num)) return String(value ?? "-");
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num);
}
