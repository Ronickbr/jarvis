import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, Bot, BrainCircuit, ChevronRight, Command, Cpu, Database,
  Gauge, LockKeyhole, MemoryStick, Mic, MicOff, Network, Send, Settings,
  ShieldCheck, Sparkles, TerminalSquare, Volume2, Wifi, Zap,
} from "lucide-react";
import { api, Evolution, Provider } from "./api";

type Message = { id: number; role: "assistant" | "user"; content: string; meta?: string };
type SpeechRecognitionCtor = new () => {
  lang: string; continuous: boolean; interimResults: boolean;
  onresult: (event: { results: ArrayLike<{ 0: { transcript: string } }> }) => void;
  onend: () => void; start: () => void; stop: () => void;
};

const starterMessages: Message[] = [{
  id: 1, role: "assistant", content: "Sistemas neurais sincronizados. Em que posso ajudar, senhor?", meta: "JARVIS · AGORA",
}];
const fallbackProviders: Provider[] = ["openai", "anthropic", "gemini", "xai"].map((name) => ({ name, configured: false, models: [] }));
const fallbackEvolution: Evolution = {
  level: 1,
  stage: "NÚCLEO",
  xp: 0,
  progress: 0,
  next_threshold: 100,
  xp_to_next: 100,
  metrics: { conversations: 0, providers_configured: 0, tools_created: 0, tools_enabled: 0, tool_executions: 0 },
};

function NeuralFace({ level, state }: { level: number; state: "idle" | "listening" | "thinking" | "speaking" }) {
  const nodes = useMemo(() => Array.from({ length: 56 }, (_, i) => ({
    x: 88 + ((i * 47) % 225), y: 34 + ((i * 83) % 328), r: i % 9 === 0 ? 2.2 : 1.15,
  })), []);
  return (
    <div className={`face-stage level-${level} is-${state}`} aria-label={`Avatar neural, nível ${level}, estado ${state}`}>
      <div className="face-halo halo-a" /><div className="face-halo halo-b" />
      <svg className="neural-face" viewBox="0 0 400 430" role="img" aria-hidden="true">
        <defs>
          <linearGradient id="faceLine" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#82fbff"/><stop offset="1" stopColor="#087985"/></linearGradient>
          <radialGradient id="eyeGlow"><stop stopColor="#fff"/><stop offset=".22" stopColor="#72fbff"/><stop offset="1" stopColor="#05a9b8" stopOpacity="0"/></radialGradient>
          <filter id="softGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
        </defs>
        <g className="scan-grid"><path d="M44 108H356M28 176H372M22 244H378M40 312H360M91 25V392M163 9V416M237 9V416M309 25V392"/></g>
        <g className="face-wire" filter="url(#softGlow)">
          <path d="M200 18C126 18 76 69 69 151c-6 74 15 180 75 232 20 18 39 29 56 31 17-2 36-13 56-31 60-52 81-158 75-232-7-82-57-133-131-133Z"/>
          <path d="M84 154l43-31 55 16 18 34 18-34 55-16 43 31M106 199l58 7 36-17 36 17 58-7M200 173l-23 82 23 18 23-18-23-82ZM126 300l46 18h56l46-18M147 345l53 22 53-22M98 106l55-48 47 23 47-23 55 48M73 238l51 62-20 45M327 238l-51 62 20 45"/>
          <path className="detail-lines" d="M109 83l18 40-43 31 22 45-33 39M291 83l-18 40 43 31-22 45 33 39M153 58l29 81-55-16-21 76 58 7-40 94 48 18-25 27M247 58l-29 81 55-16 21 76-58 7 40 94-48 18 25 27"/>
        </g>
        <g className="eyes" filter="url(#softGlow)"><ellipse cx="145" cy="180" rx="32" ry="14"/><ellipse cx="255" cy="180" rx="32" ry="14"/><circle cx="145" cy="181" r="23" fill="url(#eyeGlow)"/><circle cx="255" cy="181" r="23" fill="url(#eyeGlow)"/></g>
        <g className="face-nodes">{nodes.map((node, i) => <circle key={i} cx={node.x} cy={node.y} r={node.r}/>)}</g>
        <path className="scan-line" d="M55 0V430"/>
      </svg>
      <div className="state-readout"><i /><span>{state === "thinking" ? "PROCESSANDO" : state === "listening" ? "OUVINDO" : state === "speaking" ? "RESPONDENDO" : "AGUARDANDO"}</span><i /></div>
    </div>
  );
}

function InfoCard({ icon, label, value, detail, tone = "cyan" }: { icon: React.ReactNode; label: string; value: string; detail: string; tone?: "cyan" | "green" | "amber" }) {
  return <article className={`info-card ${tone}`}><div className="card-icon">{icon}</div><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div><ChevronRight size={14}/></article>;
}

export default function App() {
  const [messages, setMessages] = useState(starterMessages);
  const [providers, setProviders] = useState<Provider[]>(fallbackProviders);
  const [provider, setProvider] = useState("auto");
  const [activeModel, setActiveModel] = useState("Roteamento automático");
  const [lastLatency, setLastLatency] = useState<number | null>(null);
  const [evolution, setEvolution] = useState<Evolution>(fallbackEvolution);
  const [input, setInput] = useState(""); const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false); const [speaking, setSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false); const [online, setOnline] = useState(false);
  const recognition = useRef<InstanceType<SpeechRecognitionCtor> | null>(null);

  useEffect(() => {
    Promise.all([api.providers(), api.evolution()])
      .then(([items, snapshot]) => { setProviders(items); setEvolution(snapshot); setOnline(true); })
      .catch(() => setOnline(false));
  }, []);
  useEffect(() => {
    const SpeechRecognition = (window as unknown as Record<string, SpeechRecognitionCtor>).SpeechRecognition ?? (window as unknown as Record<string, SpeechRecognitionCtor>).webkitSpeechRecognition;
    if (!SpeechRecognition) return; setSpeechSupported(true); const instance = new SpeechRecognition();
    instance.lang = "pt-BR"; instance.continuous = false; instance.interimResults = false;
    instance.onresult = (event) => setInput(event.results[0][0].transcript); instance.onend = () => setListening(false); recognition.current = instance;
  }, []);

  const configured = providers.filter((item) => item.configured).length;
  const evolutionXp = evolution.progress;
  const evolutionLevel = evolution.level;
  const avatarState = busy ? "thinking" : listening ? "listening" : speaking ? "speaking" : "idle";
  function toggleListening() { if (!recognition.current) return; if (listening) recognition.current.stop(); else { setListening(true); recognition.current.start(); } }

  async function submit(event: FormEvent) {
    event.preventDefault(); const content = input.trim(); if (!content || busy) return;
    setMessages((current) => [...current, { id: Date.now(), role: "user", content }]); setInput(""); setBusy(true);
    try {
      const result = await api.chat(content, provider); setActiveModel(`${result.provider} · ${result.model}`); setLastLatency(result.latency_ms);
      setMessages((current) => [...current, { id: Date.now() + 1, role: "assistant", content: result.content, meta: `${result.provider.toUpperCase()} · ${result.model} · ${result.latency_ms} MS` }]);
      api.evolution().then(setEvolution).catch(() => undefined);
      if ("speechSynthesis" in window) { const utterance = new SpeechSynthesisUtterance(result.content); utterance.lang = "pt-BR"; utterance.rate = 1.04; utterance.onstart = () => setSpeaking(true); utterance.onend = () => setSpeaking(false); window.speechSynthesis.speak(utterance); }
    } catch (error) { setMessages((current) => [...current, { id: Date.now() + 1, role: "assistant", content: error instanceof Error ? error.message : "Não consegui alcançar o núcleo.", meta: "SISTEMA · FALHA DE CONEXÃO" }]); }
    finally { setBusy(false); }
  }

  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark"><BrainCircuit size={25}/></div><div><strong>JARVIS</strong><span>NEURAL OS</span></div></div>
      <nav aria-label="Navegação principal"><button className="nav-item active"><Command size={18}/>Central</button><button className="nav-item"><Bot size={18}/>Conversas</button><button className="nav-item"><TerminalSquare size={18}/>Ferramentas <b>{evolution.metrics.tools_created}</b></button><button className="nav-item"><Activity size={18}/>Atividade</button></nav>
      <div className="sidebar-bottom"><div className="evolution-mini"><span>EVOLUÇÃO</span><strong>NÍVEL {String(evolutionLevel).padStart(2,"0")}</strong><div><i style={{width:`${evolutionXp}%`}}/></div></div><button className="nav-item"><Settings size={18}/>Configurações</button><div className="profile"><span>RB</span><div><strong>Operador</strong><small>Acesso local</small></div></div></div>
    </aside>
    <main><header className="topbar"><div><span className={`status-dot ${online ? "online" : ""}`}/>{online ? "NÚCLEO ONLINE" : "MODO OFFLINE"}</div><div className="topbar-center"><Network size={13}/> REDE NEURAL ESTÁVEL</div><button aria-label="Configurações"><Settings size={18}/></button></header>
      <section className="dashboard"><div className="hero-copy"><p className="eyebrow"><Sparkles size={15}/> INTERFACE COGNITIVA</p><h1>JARVIS <span>NEURAL CORE</span></h1><p>Consciência digital adaptativa · Monitoramento em tempo real</p></div>
        <div className="neural-layout">
          <div className="side-cards left-cards"><p className="rail-title">SISTEMAS</p><InfoCard icon={<Wifi size={17}/>} label="NÚCLEO" value={online ? "ONLINE" : "LOCAL"} detail={online ? "API sincronizada" : "Modo demonstração"} tone="green"/><InfoCard icon={<Cpu size={17}/>} label="MODELO ATIVO" value={provider === "auto" ? "AUTO" : provider.toUpperCase()} detail={activeModel}/><InfoCard icon={<Gauge size={17}/>} label="LATÊNCIA" value={lastLatency ? `${lastLatency} ms` : "— ms"} detail={lastLatency && lastLatency < 2500 ? "Dentro da meta" : "Aguardando amostra"}/></div>
          <div className="face-column"><div className="level-badge"><span>NÍVEL {String(evolutionLevel).padStart(2,"0")}</span><strong>{evolution.stage}</strong></div><NeuralFace level={evolutionLevel} state={avatarState}/><div className="evolution-track"><div><span>EVOLUÇÃO NEURAL</span><strong>{evolutionXp}%</strong></div><div className="track"><i style={{width:`${evolutionXp}%`}}/></div><small>{evolution.next_threshold ? `${evolution.xp_to_next} XP PARA O PRÓXIMO MARCO` : "NÍVEL MÁXIMO ATINGIDO"}</small></div></div>
          <div className="side-cards right-cards"><p className="rail-title">INTELIGÊNCIA</p><InfoCard icon={<MemoryStick size={17}/>} label="MEMÓRIA" value={`${evolution.metrics.conversations} CICLOS`} detail={`${evolution.metrics.tool_executions} tools executadas`}/><InfoCard icon={<ShieldCheck size={17}/>} label="SEGURANÇA" value="PROTEGIDO" detail={`${evolution.metrics.tools_enabled} tools aprovadas`} tone="green"/><InfoCard icon={<Volume2 size={17}/>} label="VOZ" value="PT-BR" detail={speechSupported ? "Reconhecimento pronto" : "Entrada por texto"}/></div>
        </div>
        <section className="workspace-card"><div className="conversation" aria-live="polite">{messages.map((message) => <div className={`message ${message.role}`} key={message.id}><div className="avatar">{message.role === "assistant" ? <Bot size={18}/> : "R"}</div><div><small>{message.meta ?? "VOCÊ · AGORA"}</small><p>{message.content}</p></div></div>)}{busy && <div className="typing"><i/><i/><i/></div>}</div>
          <form onSubmit={submit} className="composer"><button type="button" className={`mic ${listening ? "listening" : ""}`} onClick={toggleListening} disabled={!speechSupported} aria-label={listening ? "Parar de ouvir" : "Iniciar comando de voz"}>{listening ? <MicOff size={20}/> : <Mic size={20}/>}</button><label><span className="sr-only">Comando</span><input value={input} onChange={(event)=>setInput(event.target.value)} placeholder="Diga ou digite uma instrução para o núcleo..." maxLength={50000}/></label><select value={provider} onChange={(event)=>setProvider(event.target.value)} aria-label="Provedor"><option value="auto">AUTO</option>{providers.map((item)=><option key={item.name} value={item.name}>{item.name.toUpperCase()}</option>)}</select><button type="submit" className="send" disabled={busy || !input.trim()} aria-label="Enviar"><Send size={19}/></button></form>
        </section>
        <div className="system-strip"><span><Zap size={13}/> {configured}/4 PROVIDERS</span><span><LockKeyhole size={13}/> SANDBOX ISOLADO</span><span><Database size={13}/> REGISTRO AUDITÁVEL</span></div>
      </section></main>
  </div>;
}
