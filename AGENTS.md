# Jarvis — instruções para agentes

## Princípios

- Segurança precede autonomia.
- Toda ação externa deve ser classificada como leitura, escrita, sensível ou destrutiva.
- Escritas sensíveis e ações destrutivas exigem confirmação humana imediatamente antes da execução.
- Código gerado nunca roda diretamente no processo da API.
- Segredos nunca entram em prompts, logs, banco ou repositório.

## Qualidade

- Mudanças estruturais exigem atualização de `docs/architecture.md`.
- Novas tools exigem schema, permissões, testes e trilha de auditoria.
- Provedores de LLM devem implementar o contrato comum e possuir fallback.
- Execute os testes de backend e frontend antes de abrir PR.

## Limites

- Não alegar isolamento forte quando o executor Docker não estiver ativo.
- Não habilitar rede no sandbox por padrão.
- Não executar código gerado sem aprovação explícita no MVP.
