import axios from "axios";

const BASE = (import.meta.env?.VITE_JARVIS_API as string | undefined) ?? "http://127.0.0.1:8001";

export async function listTools() {
  const { data } = await axios.get(`${BASE}/tools`);
  return data;
}

export async function runTool(tool: string, args: Record<string, unknown> = {}) {
  const { data } = await axios.post(`${BASE}/run-tool`, { tool, args });
  return data;
}

export async function runPlan(steps: Array<Record<string, unknown>>) {
  const { data } = await axios.post(`${BASE}/run-plan`, { steps });
  return data;
}

export async function runNL(message: string): Promise<{ text: string; meta?: Record<string, unknown> }> {
  const { data } = await axios.post(`${BASE}/nl`, { message });
  return data;
}

export async function listServers() {
  const { data } = await axios.get(`${BASE}/servers`);
  return data as { default: string; servers: Array<Record<string, any>> };
}

export async function connectServer(payload: {
  alias: string;
  command: string;
  args?: string[];
  save?: boolean;
  cwd?: string | null;
  env?: Record<string, string> | null;
}) {
  const { data } = await axios.post(`${BASE}/servers/connect`, payload);
  return data;
}

export async function disconnectServer(alias: string, options: { forget?: boolean } = {}) {
  const { data } = await axios.post(`${BASE}/servers/disconnect`, { alias, ...options });
  return data;
}
