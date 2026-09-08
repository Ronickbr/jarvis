# Como contribuir

1. Crie uma branch a partir de `main`.
2. Mantenha alterações pequenas, com testes e documentação correspondente.
3. Nunca adicione credenciais, `.env`, dumps de conversa ou dados pessoais.
4. Execute `pytest`, `ruff check services/api` e `npm --prefix apps/web run build`.
5. Abra um pull request explicando problema, solução, risco e evidências de teste.

Novos provedores devem implementar o contrato comum e falhar sem expor detalhes de credenciais. Novas tools precisam declarar schema, permissões, risco esperado e testes de política.
