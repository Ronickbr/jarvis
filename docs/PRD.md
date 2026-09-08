# PRD — Jarvis

**Versão:** 1.1
**Data:** 08 de setembro de 2026
**Status:** Aprovado para fundação técnica

## Visão

Assistente pessoal voice-first, multi-LLM e extensível, com personalidade elegante e sarcástica configurável. O sistema transforma linguagem natural em respostas e ações auditáveis, mantendo confirmação humana para operações críticas.

> O produto é inspirado na categoria de assistentes ficcionais, sem utilizar voz, identidade visual ou ativos protegidos de franquias.

## Resultado do MVP

O usuário conversa por texto ou voz, escolhe roteamento automático ou manual, acompanha qual modelo respondeu e cria tools em estado de rascunho. O sistema valida a definição, solicita aprovação e executa somente em sandbox configurado.

## Escopo

### Fundação entregue

- HUD web responsivo e shell Tauri.
- API FastAPI com health check e contratos versionados.
- Roteador para OpenAI, Anthropic, Gemini e xAI.
- Política de risco e confirmação de ações.
- Registro persistente de tools e auditoria.
- Executor Docker sem rede por padrão.
- Voz no navegador usando Web Speech API quando disponível.

### Próximas fases

- Whisper e Piper locais.
- Streaming de voz full duplex e barge-in.
- Métricas reais de custo/latência e circuit breaker.
- Memória vetorial e recuperação semântica.
- Assinatura de tools, marketplace e permissões por workspace.

## Critérios de aceite da fundação

- API inicia sem chaves e informa provedores indisponíveis.
- Roteamento automático nunca seleciona provedor sem credencial.
- Ações críticas retornam estado `confirmation_required`.
- Código em rascunho não é executável.
- Testes de política e roteamento passam sem chamadas externas.
- Frontend funciona com respostas simuladas quando nenhum provedor está configurado.
