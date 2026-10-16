# Fluxo híbrido — Guia de Ponto Cruz v0.9.2

## Conceito
A parte artística fica fora do app e é gerada no ChatGPT com um prompt montado pelo próprio sistema.
Depois, a imagem aprovada é importada e o aplicativo executa a parte técnica do gráfico.

## Etapas
1. **Prompt + base artística**
   - escolher matriz desejada;
   - escolher limite visual de cores;
   - escolher com ou sem contorno;
   - copiar prompt;
   - gerar imagem no ChatGPT;
   - importar imagem aprovada.
2. **Tamanho e enquadramento**
   - confirmar/ajustar grade final e recorte.
3. **Cores essenciais**
   - proteger cores críticas, se necessário.
4. **Matriz bordável**
   - converter para 1 célula = 1 ponto.
5. **Paleta e simplificação**
   - reduzir a paleta e remover redundâncias.
6. **Edição manual**
   - corrigir pontos sensíveis.
7. **Gráfico e legenda**
   - gerar molde técnico.
8. **Exportar**
   - salvar arquivos finais.

## Benefício principal
O app passa a conter a lógica do prompt, sem depender de API, e você não precisa montar manualmente o texto a cada novo projeto.
