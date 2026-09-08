import { FormEvent, useEffect, useRef, useState } from "react";
import {
  Activity,
  Bot,
  BrainCircuit,
  Command,
  Cpu,
  Gauge,
  Mic,
  MicOff,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  Volume2,
} from "lucide-react";
import { api, Provider } from "./api";

type Message = {
  id: number;
  role: "assistant" | "user";
  content: string;
  meta?: string;
};

type SpeechRecognitionCtor = new () => {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: (event: { results: ArrayLike<{ 0: { transcript: string } }> }) => void;
  onend: () => void;
  start: () => void;
  stop: () => void;
};

const starterMessages: Message[] = [
  {
    id: 1,
    role: "assistant",
    content: "Sistemas prontos. Em que posso ajudar hoje?",
    meta: "JARVIS · AGORA",
  },
];

const fallbackProviders: Provider[] = ["openai", "anthropic", "gemini", "xai"].map((name) => ({
  name,
  configured: false,
  models: [],
}));

export default function App() {
  const [messages, setMessages] = useState(starterMessages);
  const [providers, setProviders] = useState<Provider[]>(fallbackProviders);
  const [provider, setProvider] = useState("auto");
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [online, setOnline] = useState(false);
  const recognition = useRef<InstanceType<SpeechRecognitionCtor> | null>(null);

  useEffect(() => {
    api.providers()
      .then((items) => {
        setProviders(items);
        setOnline(true);
      })
      .catch(() => setOnline(false));
  }, []);

  useEffect(() => {
    const SpeechRecognition = (window as unknown as Record<string, SpeechRecognitionCtor>)
      .SpeechRecognition ??
      (window as unknown as Record<string, SpeechRecognitionCtor>).webkitSpeechRecognition;
    if (!SpeechRecognition) return;
    setSpeechSupported(true);
    const instance = new SpeechRecognition();
    instance.lang = "pt-BR";
    instance.continuous = false;
    instance.interimResults = false;
    instance.onresult = (event) => setInput(event.results[0][0].transcript);
    instance.onend = () => setListening(false);
    recognition.current = instance;
  }, []);

  function toggleListening() {
    if (!recognition.current) return;
    if (listening) {
      recognition.current.stop();
    } else {
      setListening(true);
      recognition.current.start();
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || busy) return;
    setMessages((current) => [...current, { id: Date.now(), role: "user", content }]);
    setInput("");
    setBusy(true);
    try {
      const result = await api.chat(content, provider);
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: result.content,
          meta: `${result.provider.toUpperCase()} · ${result.model} · ${result.latency_ms} MS`,
        },
      ]);
      if ("speechSynthesis" in window) {
        const utterance = new SpeechSynthesisUtterance(result.content);
        utterance.lang = "pt-BR";
        utterance.rate = 1.04;
        window.speechSynthesis.speak(utterance);
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: error instanceof Error ? error.message : "Não consegui alcançar o núcleo.",
          meta: "SISTEMA · FALHA DE CONEXÃO",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  const configured = providers.filter((item) => item.configured).length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><BrainCircuit size={25} /></div>
          <div><strong>JARVIS</strong><span>COMMAND OS</span></div>
        </div>
        <nav aria-label="Navegação principal">
          <button className="nav-item active"><Command size={18} />Central</button>
          <button className="nav-item"><Bot size={18} />Conversas</button>
          <button className="nav-item"><TerminalSquare size={18} />Ferramentas <b>0</b></button>
          <button className="nav-item"><Activity size={18} />Atividade</button>
        </nav>
        <div className="sidebar-bottom">
          <button className="nav-item"><Settings size={18} />Configurações</button>
          <div className="profile"><span>RS</span><div><strong>Operador</strong><small>Acesso local</small></div></div>
        </div>
      </aside>

      <main>
        <header className="topbar">
          <div><span className={`status-dot ${online ? "online" : ""}`} />{online ? "NÚCLEO ONLINE" : "MODO OFFLINE"}</div>
          <p>08 SET 2026 <span>•</span> 21:42 UTC</p>
          <button aria-label="Configurações"><Settings size={18} /></button>
        </header>

        <section className="dashboard">
          <div className="hero-copy">
            <p className="eyebrow"><Sparkles size={15} /> ASSISTENTE OPERACIONAL</p>
            <h1>Boa noite, <span>senhor.</span></h1>
            <p>Todos os sistemas estão operacionais. Aguardando sua próxima instrução.</p>
          </div>

          <div className={`core ${busy ? "thinking" : ""}`} aria-label={busy ? "Processando" : "Aguardando comando"}>
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="core-center"><Cpu size={42} /><span>{busy ? "ANALISANDO" : "PRONTO"}</span></div>
          </div>

          <div className="stats">
            <article><Gauge size={19} /><div><span>PROVEDORES</span><strong>{configured}<small>/4</small></strong></div></article>
            <article><ShieldCheck size={19} /><div><span>POLÍTICA</span><strong>ATIVA</strong></div></article>
            <article><Volume2 size={19} /><div><span>VOZ</span><strong>PT-BR</strong></div></article>
          </div>

          <section className="workspace-card">
            <div className="conversation" aria-live="polite">
              {messages.map((message) => (
                <div className={`message ${message.role}`} key={message.id}>
                  <div className="avatar">{message.role === "assistant" ? <Bot size={18} /> : "R"}</div>
                  <div><small>{message.meta ?? "VOCÊ · AGORA"}</small><p>{message.content}</p></div>
                </div>
              ))}
              {busy && <div className="typing"><i /><i /><i /></div>}
            </div>

            <form onSubmit={submit} className="composer">
              <button
                type="button"
                className={`mic ${listening ? "listening" : ""}`}
                onClick={toggleListening}
                disabled={!speechSupported}
                aria-label={listening ? "Parar de ouvir" : "Iniciar comando de voz"}
              >
                {listening ? <MicOff size={20} /> : <Mic size={20} />}
              </button>
              <label>
                <span className="sr-only">Comando</span>
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Diga ou digite uma instrução..."
                  maxLength={50000}
                />
              </label>
              <select value={provider} onChange={(event) => setProvider(event.target.value)} aria-label="Provedor">
                <option value="auto">AUTO</option>
                {providers.map((item) => <option key={item.name} value={item.name}>{item.name.toUpperCase()}</option>)}
              </select>
              <button type="submit" className="send" disabled={busy || !input.trim()} aria-label="Enviar"><Send size={19} /></button>
            </form>
          </section>

          <div className="provider-row">
            {providers.map((item) => (
              <div className="provider-chip" key={item.name}>
                <span className={item.configured ? "available" : ""} />
                <div><strong>{item.name}</strong><small>{item.configured ? "disponível" : "sem chave"}</small></div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
