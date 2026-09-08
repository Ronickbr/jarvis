# Política de segurança

## Versões suportadas

Somente a versão mais recente da linha `0.x` recebe correções durante o MVP.

## Reporte responsável

Não publique vulnerabilidades em issues abertas. Use o recurso **Security → Report a vulnerability** do GitHub. Inclua impacto, reprodução mínima e versão afetada; não inclua chaves, tokens ou dados pessoais.

## Modelo de ameaça do MVP

- A API `v0.1.0` é local e single-user; não deve ser exposta diretamente à internet.
- Código gerado é não confiável e só pode rodar após validação e aprovação.
- A execução exige Docker e inicia sem rede, filesystem gravável ou capabilities Linux.
- Operações de alto risco exigem confirmação imediatamente antes da execução.
- O sandbox é defesa em profundidade, não garantia absoluta de isolamento.
