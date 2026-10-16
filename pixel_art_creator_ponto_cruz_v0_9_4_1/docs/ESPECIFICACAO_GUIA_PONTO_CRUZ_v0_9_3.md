# Especificação funcional — Guia de Ponto Cruz v0.9.3

## Objetivo
Corrigir a etapa de matriz bordável para que a redução artística para 50×50/100×100 seja feita pelo ChatGPT via prompt e não por uma conversão mecânica do sistema.

## Arquitetura híbrida

### Parte artística — ChatGPT
- criação da base artística;
- redesenho orientado para a matriz-alvo;
- simplificação visual inicial da paleta;
- preservação de expressão e detalhes focais.

### Parte técnica — aplicativo
- importação;
- normalização exata da grade;
- levantamento de paleta;
- proteção opcional de essenciais;
- revisão/redução técnica opcional;
- edição manual;
- gráfico, legenda e exportação.

## Fluxo implementado

### 1. Base artística + prompt inicial
Importa a base ilustrada aprovada.

### 2. Matriz artística via Chat
Configura:
- largura/altura 50–100;
- limite visual 8–50 cores;
- contorno sim/não.

O app monta o prompt de redesenho e permite copiar/salvar TXT.
Depois a usuária importa o resultado do ChatGPT.

### 3. Normalização técnica
Modo padrão: **Preservação máxima**.
- nearest-neighbor;
- 1 célula = 1 RGB sólido;
- sem média;
- sem mediana;
- sem redesenho artístico.

Modo alternativo: **Conversão automática experimental** com o método anterior.

### 4. Cores essenciais
Opcional.

### 5. Paleta técnica
Se o número de cores já estiver dentro do limite:
- usar a paleta atual;
- sem remapeamento;
- sem alteração das células.

Se ultrapassar o limite:
- recomendação principal: voltar ao Chat e gerar nova matriz artística;
- alternativa: simplificação local experimental.

### 6–8. Etapas técnicas finais
Edição manual, gráfico/legenda e exportação.

## Critérios de aceitação
- matriz 50×50 criada artisticamente no Chat antes da normalização;
- etapa local não usa redução mediana como padrão;
- olhos e focinho dependem prioritariamente da imagem artística importada;
- imagem dentro do limite de cores pode avançar sem simplificação local;
- modo automático antigo continua disponível apenas como experimental.
