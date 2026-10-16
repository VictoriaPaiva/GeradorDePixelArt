# ESPECIFICAÇÃO OFICIAL REFORMULADA — GERADOR DE GUIA DE BORDADO EM PONTO CRUZ

**Projeto:** Pixel Art Creator / Cross-Stitch Guide Creator  
**Versão conceitual:** v0.9 — Reformulação de objetivo e fluxo  
**Data:** 15/10/2026  
**Status:** especificação definida; implementação ainda não iniciada

## 1. Objetivo real do projeto

O objetivo principal do sistema não é apenas gerar uma imagem bonita em pixel art. O objetivo é **transformar uma imagem de referência em um gráfico utilizável de bordado em ponto cruz**.

A pixel art é uma etapa intermediária para simplificar artisticamente a imagem. O produto final é um **mapa de pontos**, no qual:

- cada célula da grade corresponde a **um ponto de bordado**;
- cada célula possui **uma única cor sólida**;
- a quantidade de linhas e colunas é conhecida e limitada;
- a paleta é limitada para que seja viável separar os fios;
- o resultado pode ser impresso/consultado como um gráfico de ponto cruz, com grade, códigos e legenda.

## 2. Papel da IA

A IA é usada apenas para produzir uma **base artística simplificada e com aparência de desenho/cartoon**, a partir da imagem original.

### Regra de arquitetura

A geração artística acontece **no ChatGPT por meio de um prompt padrão**. O aplicativo local **não usa API**, não solicita `OPENAI_API_KEY` e não depende de créditos de API.

### O que a IA deve fazer

- preservar o reconhecimento, a pose, a composição e os elementos importantes da imagem;
- transformar a referência em uma ilustração mais desenhada e menos fotográfica;
- trabalhar com massas de cor, mechas e planos mais claros;
- usar cores vivas e artisticamente organizadas, sem ficar presa às cores fotográficas exatas;
- reduzir microdetalhes que não sobreviveriam ao bordado;
- separar melhor sombra, meio-tom e luz;
- evitar ruído e excesso de nuances semelhantes;
- não inventar brilhos ou detalhes decorativos desnecessários.

### O que a IA NÃO precisa fazer

- garantir exatamente 50×50, 75×75 ou 100×100 células;
- gerar a grade final;
- gerar códigos ou legenda;
- limitar a paleta final de fios;
- garantir uma célula lógica perfeita por ponto de bordado.

Essas tarefas pertencem ao sistema determinístico.

## 3. Papel do sistema local

O aplicativo recebe a **base ilustrada já gerada/aprovada no ChatGPT** e a converte em um gráfico técnico de ponto cruz.

O sistema é responsável por:

1. enquadrar/cortar a imagem;
2. definir a quantidade exata de pontos na largura e altura;
3. transformar a imagem em uma matriz lógica de pontos;
4. garantir uma única cor sólida por célula;
5. reduzir a paleta para o limite escolhido;
6. permitir revisão/remoção/união de cores semelhantes;
7. permitir edição manual célula a célula;
8. gerar grade, símbolos/códigos e legenda;
9. exportar o gráfico final.

## 4. Novo fluxo oficial

### Etapa 1 — Base artística / Importação

- Exibir dois prompts oficiais: **sem contorno** e **com contorno**.
- Botão para copiar o prompt.
- A usuária gera a imagem no ChatGPT usando a fotografia original como referência.
- A versão aprovada é importada no aplicativo.
- O aplicativo não chama nenhuma API de geração.

### Etapa 2 — Tamanho e enquadramento do bordado

A usuária define o tamanho real do gráfico em pontos.

#### Presets sugeridos

- 50×50
- 75×75
- 100×100

#### Modo personalizado

- largura e altura configuráveis;
- faixa inicial recomendada: **20 a 100 pontos por eixo**;
- opção de manter a proporção original;
- opção de cortar para preencher a grade ou encaixar a imagem inteira;
- a imagem não precisa ser quadrada: por exemplo, 50×38, 72×100 ou 86×64 são válidos.

**Regra:** 1 célula lógica = 1 ponto de bordado.

### Etapa 3 — Conversão para matriz bordável

A imagem é convertida para a grade exata selecionada.

Requisitos:

- exatamente `largura × altura` células;
- cada célula recebe apenas **uma cor sólida**;
- nenhuma célula pode conter mescla, gradiente ou subpixel;
- não usar anti-aliasing na matriz final;
- não adicionar linhas de grade à matriz técnica;
- a grade é apenas uma camada de visualização.

A cor representativa de cada célula deve ser determinada de forma determinística a partir da região correspondente da imagem-base.

### Etapa 4 — Paleta e simplificação de cores

A matriz inicial pode possuir muitas cores. O sistema reduz a paleta para um limite definido pela usuária.

#### Limite de cores

- padrão recomendado: **até 50 cores**;
- permitir valores menores, por exemplo 10, 20, 30, 40 ou 50;
- o objetivo é representar uma quantidade viável de fios, não obrigar o uso de 50 cores.

#### Regras

- sem dithering aleatório;
- cores visualmente parecidas devem ser apresentadas próximas umas das outras;
- a usuária pode marcar cores redundantes para remoção;
- ao remover uma cor, a imagem é recalculada usando **somente as cores restantes**;
- não preencher novamente a paleta até o máximo automaticamente;
- permitir proteger cores importantes como essenciais;
- as cores essenciais devem ser opcionais, e não uma etapa obrigatória para gerar o primeiro gráfico.

### Etapa 5 — Limpeza de pontos e edição manual

O editor trabalha diretamente sobre a grade de pontos.

Requisitos:

- clique pinta uma célula inteira;
- conta-gotas;
- desfazer/refazer;
- zoom e pan;
- somente cores da paleta final;
- opção futura de detectar pontos isolados ou pequenos grupos que criem “ruído” no bordado.

#### Regra importante para bordado

Um pixel isolado representa um ponto isolado de linha. Portanto, o sistema deve futuramente oferecer uma ferramenta de **limpeza de pontos isolados**, com pré-visualização e aprovação, sem alterar automaticamente detalhes importantes.

### Etapa 6 — Gráfico de ponto cruz

Gerar um gráfico técnico como os exemplos fornecidos pela usuária.

Elementos:

- grade de uma célula por ponto;
- linhas mais fortes a cada 5 ou 10 células;
- numeração de linhas e colunas;
- símbolo ou código dentro de cada célula;
- uma identificação única por cor;
- legenda completa;
- contagem de pontos por cor;
- percentual por cor;
- dimensão total da grade.

### Etapa 7 — Exportação

Arquivos previstos:

- matriz técnica sem grade;
- preview ampliado;
- imagem com grade;
- gráfico codificado;
- legenda;
- JSON / CSV / TXT;
- **PDF pronto para impressão** como prioridade do novo fluxo.

O PDF deverá futuramente suportar gráficos grandes divididos em páginas, mantendo referência de linhas/colunas.

## 5. Mudança importante: áreas e cores essenciais

O fluxo anterior tornava a seleção de áreas e cores essenciais uma parte central e obrigatória. Para o objetivo de ponto cruz isso adiciona trabalho demais antes de obter um primeiro resultado.

### Nova decisão

A criação de áreas passa a ser uma **ferramenta avançada/opcional**.

O fluxo básico deve conseguir:

`Importar base → definir grade → gerar matriz → reduzir paleta → editar → gerar gráfico`

sem exigir que a usuária pinte regiões manualmente.

As cores essenciais permanecem disponíveis para casos em que seja importante proteger um tom específico, como:

- cor da coleira;
- olhos;
- roupa;
- símbolo;
- elemento importante do personagem.

## 6. Tratamento de proporção

O sistema não deve presumir que todo bordado é quadrado.

Exemplos válidos:

- 50×50;
- 50×34;
- 63×75;
- 80×55;
- 100×100.

A usuária poderá:

- travar proporção;
- informar somente a largura e calcular a altura automaticamente;
- informar somente a altura e calcular a largura;
- destravar a proporção para um tamanho específico, com aviso caso isso distorça a imagem.

## 7. Fundo da imagem

O fundo interfere diretamente na quantidade de pontos e cores.

Planejar uma opção:

- **bordar fundo**;
- **ignorar fundo** / tratar como área vazia;
- futuramente permitir máscara manual de fundo.

Essa funcionalidade é importante, mas pode ser implementada depois do novo fluxo básico.

## 8. Paleta de linhas de bordado

A primeira versão pode continuar usando RGB/HEX genérico.

Como evolução futura, o sistema poderá converter a paleta para catálogos reais de linhas, como:

- DMC;
- Anchor;
- outros catálogos configuráveis.

Esse mapeamento deve ser tratado como uma etapa posterior, porque exige uma tabela confiável de cores comerciais.

## 9. Prompt padrão da IA

O prompt padrão não deve pedir à IA para gerar a grade final exata. Isso é responsabilidade do sistema.

O prompt deve pedir uma **base ilustrada adequada para conversão em ponto cruz**, com:

- aparência cartoon/pixel art desenhada;
- formas legíveis;
- cores vivas e separadas;
- poucos microdetalhes;
- grandes regiões visuais coerentes;
- sombras e luzes simplificadas;
- sem anti-aliasing intencional;
- sem grade, códigos, números ou legenda;
- versão sem contorno e versão com contorno.

## 10. Prompt oficial — SEM contorno

Use a imagem anexada como referência e transforme-a em uma ILUSTRAÇÃO EM PIXEL ART/CARTOON pensada como BASE PARA UM GRÁFICO DE BORDADO EM PONTO CRUZ.

O objetivo não é reproduzir a fotografia pixel por pixel. O objetivo é criar uma versão desenhada, simplificada, colorida e claramente reconhecível, que depois será convertida pelo sistema para uma grade exata de pontos.

PRIORIDADES:
- preserve composição, pose, proporções, silhueta, expressão e elementos característicos;
- preserve cores realmente importantes para reconhecer o sujeito, mas trate as demais cores com liberdade artística;
- use uma paleta mais viva, alegre e ilustrada do que a fotografia, com contraste claro entre as principais famílias de cor;
- simplifique detalhes fotográficos pequenos;
- agrupe pelos, cabelos, vegetação e texturas em mechas, massas e formas gráficas maiores;
- organize sombra, meio-tom e luz em faixas claramente diferenciadas;
- evite muitas nuances quase iguais;
- evite ruído de pequenos detalhes isolados que não seriam úteis em um bordado;
- cada bloco/pixel visível deve ter uma única cor sólida;
- não use blur, anti-aliasing, gradientes suaves ou mistura de cores dentro do mesmo bloco;
- não invente brilhos, reflexos ou pontos de luz decorativos;
- não adicione textos, grade, números, símbolos ou legenda.

CONTORNO:
- não adicione contorno preto ou line art artificial;
- diferencie as formas por contraste de cor, sombra e luz;
- preserve apenas linhas naturalmente escuras que façam parte da referência.

IMPORTANTE:
- não precisa gerar exatamente 50×50 ou 100×100;
- não desenhe uma grade por cima da imagem;
- o sistema fará posteriormente a conversão para a grade exata e a limitação da paleta.

## 11. Prompt oficial — COM contorno

Use a imagem anexada como referência e transforme-a em uma ILUSTRAÇÃO EM PIXEL ART/CARTOON pensada como BASE PARA UM GRÁFICO DE BORDADO EM PONTO CRUZ.

O objetivo não é reproduzir a fotografia pixel por pixel. O objetivo é criar uma versão desenhada, simplificada, colorida e claramente reconhecível, que depois será convertida pelo sistema para uma grade exata de pontos.

PRIORIDADES:
- preserve composição, pose, proporções, silhueta, expressão e elementos característicos;
- preserve cores realmente importantes para reconhecer o sujeito, mas trate as demais cores com liberdade artística;
- use uma paleta mais viva, alegre e ilustrada do que a fotografia, com contraste claro entre as principais famílias de cor;
- simplifique detalhes fotográficos pequenos;
- agrupe pelos, cabelos, vegetação e texturas em mechas, massas e formas gráficas maiores;
- organize sombra, meio-tom e luz em faixas claramente diferenciadas;
- evite muitas nuances quase iguais;
- evite ruído de pequenos detalhes isolados que não seriam úteis em um bordado;
- cada bloco/pixel visível deve ter uma única cor sólida;
- não use blur, anti-aliasing, gradientes suaves ou mistura de cores dentro do mesmo bloco;
- não invente brilhos, reflexos ou pontos de luz decorativos;
- não adicione textos, grade, números, símbolos ou legenda.

CONTORNO:
- adicione contorno seletivo para reforçar a leitura das formas principais;
- prefira tons escuros harmonizados com a paleta, em vez de preto puro em toda a imagem;
- não contorne cada detalhe interno;
- não use linhas excessivamente grossas;
- o contorno deve ajudar a leitura do futuro bordado, sem substituir sombra, meio-tom e luz.

IMPORTANTE:
- não precisa gerar exatamente 50×50 ou 100×100;
- não desenhe uma grade por cima da imagem;
- o sistema fará posteriormente a conversão para a grade exata e a limitação da paleta.

## 12. Critérios de sucesso

Um resultado é considerado bom quando:

1. a imagem continua reconhecível;
2. a base artística parece desenho/cartoon, não apenas uma foto pixelizada;
3. a matriz possui exatamente as dimensões de pontos escolhidas;
4. cada célula tem apenas uma cor;
5. a quantidade de cores respeita o limite definido;
6. o gráfico é legível célula a célula;
7. cada cor possui código/símbolo e legenda;
8. o guia pode ser usado diretamente para executar o bordado em ponto cruz.

## 13. Próximo ciclo de implementação

### Prioridade 1
Redesenhar o fluxo do aplicativo para tornar **tamanho do bordado** uma etapa explícita e tornar **áreas/essenciais opcionais**.

### Prioridade 2
Implementar matriz configurável (50×50, 75×75, 100×100 e personalizado) com preservação de proporção.

### Prioridade 3
Reformular a simplificação para trabalhar com um **máximo de cores escolhido**, e não com meta obrigatória de 50.

### Prioridade 4
Adaptar editor, molde, legenda e exportação para matrizes retangulares e tamanhos variáveis.

### Prioridade 5
Implementar PDF pronto para impressão e, depois, avaliar limpeza de pontos isolados e mapeamento para linhas comerciais.
