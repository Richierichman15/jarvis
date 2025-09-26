import axios from "axios";

const BASE = (import.meta.env?.VITE_JARVIS_API as string | undefined) ?? "http://127.0.0.1:8001";

export async function listTools() {
  const { data } = await axios.get(`${BASE}/tools`);
  return data;
}

export async function runTool(tool: string, args: any = {}) {
  const { data } = await axios.post(`${BASE}/run-tool`, { tool, args });
  return data;
}

export async function runPlan(steps: any[]) {
  const { data } = await axios.post(`${BASE}/run-plan`, { steps });
  return data;
}

export async function runNL(message: string) {
  const { data } = await axios.post(`${BASE}/nl`, { message });
  return data;
}
