export type Provider = {
  name: string;
  configured: boolean;
  models: string[];
};

export type Evolution = {
  level: number;
  stage: string;
  xp: number;
  progress: number;
  next_threshold: number | null;
  xp_to_next: number;
  metrics: {
    conversations: number;
    providers_configured: number;
    tools_created: number;
    tools_enabled: number;
    tool_executions: number;
  };
};

export type ChatResult = {
  content: string;
  provider: string;
  model: string;
  reason: string;
  latency_ms: number;
  demo: boolean;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Erro HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  evolution: () => request<Evolution>("/api/v1/evolution"),
  providers: () => request<Provider[]>("/api/v1/providers"),
  chat: (content: string, provider: string) =>
    request<ChatResult>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ messages: [{ role: "user", content }], provider }),
    }),
};
