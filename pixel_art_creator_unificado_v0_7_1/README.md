# Pixel Art Creator — Sistema Unificado v0.7.1

Primeira versão estrutural da aplicação unificada.

## O que já funciona nesta versão

- janela principal única;
- menu lateral com as 9 etapas oficiais;
- navegação Voltar / Próximo;
- aprovação individual por etapa;
- bloqueio de avanço enquanto a etapa atual não estiver aprovada;
- carregamento e preview da imagem original;
- importação temporária de Pixel Art já gerada;
- criação, salvamento e abertura de projeto;
- `ProjectState` central;
- parâmetros oficiais:
  - matriz 100×100;
  - paleta final de 50 cores;
- páginas estruturais para todas as etapas futuras.

## O que esta versão ainda NÃO integra

Ainda não foram incorporados nesta v0.1:

- geração direta por IA;
- seletor de áreas/paleta;
- seleção das cores essenciais;
- algoritmo de matriz 100×100;
- simplificação para 50 cores;
- editor manual;
- Pattern Generator.

Esses módulos serão migrados gradualmente das versões já aprovadas.

## Programas de referência aprovados

- `pixel_art_palette_selector_v0_6_1`
- `pixel_art_manual_editor_v0_1_4`
- `pixel_art_pattern_generator_v0_1`

## Fluxo da versão final

1. Imagem
2. Pixel Art IA
3. Áreas e paletas
4. Cores essenciais
5. Matriz 100×100
6. Simplificação 50 cores
7. Edição manual
8. Molde e legenda
9. Exportar

## Instalação no Windows PowerShell

Entre na pasta do projeto e execute:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Observação sobre projeto salvo

A v0.1 salva o estado em um arquivo:

`*.pixelart.json`

Neste primeiro estágio os caminhos dos arquivos são registrados no projeto.
Nas próximas versões será adicionada uma estrutura de projeto/pasta para manter cópias
dos arquivos necessários e permitir portabilidade.


## Novidades da v0.2

A etapa de paletas deixou de ser placeholder e agora está integrada ao sistema unificado.

### Etapa 3 — Áreas e paletas
- usa a Pixel Art aprovada/importada na etapa 2;
- pintura de máscaras por região;
- criação e nomeação de áreas;
- agrupamento de cores por área;
- controle de similaridade;
- até 200 cores por área;
- hover do título para destacar a região;
- hover de cor para localizar tons correspondentes;
- recalcular paleta;
- excluir apenas a paleta;
- excluir a área.

### Etapa 4 — Cores essenciais
- seleção pelos cartões;
- seleção direta clicando na imagem;
- cores essenciais sobem para o topo da área;
- contador por área;
- contador total bruto de seleções;
- contador de RGBs únicos sem duplicação;
- exportação JSON, CSV e TXT.

### Persistência
Áreas, máscaras, paletas e seleções essenciais passam a ser gravadas dentro do
`.pixelart.json` por meio do `ProjectState`.

## Próxima etapa prevista após aprovação da v0.2
Integração da matriz lógica 100×100.


## Correção v0.2.1 — preview sem recorte

Foi corrigido o preview das etapas de imagem e Pixel Art.

- a imagem inteira agora é sempre encaixada na área disponível;
- a proporção original é preservada;
- nenhuma borda é cortada;
- quando sobra espaço, aparecem apenas margens no preview;
- a correção é somente visual e não modifica o arquivo original.


## Correção v0.2.2 — canvas das etapas 3 e 4

Foi corrigido o recorte visual que podia ocorrer nas telas de **Áreas e paletas** e **Cores essenciais**.

Causa:
- o `MaskCanvas` tinha tamanho mínimo de 520×520;
- somado aos títulos, controles e rodapé, a página podia ficar mais alta que a região útil da janela;
- a parte inferior do canvas permanecia atrás do rodapé, dando a impressão de imagem cortada.

Correção:
- o canvas agora pode reduzir de tamanho conforme a janela;
- mantém política expansível quando existe espaço;
- a imagem continua usando `KeepAspectRatio` lógico pelo cálculo interno de encaixe;
- máscaras e coordenadas continuam sendo calculadas sobre a imagem inteira.

A correção é apenas de layout/exibição e não altera máscaras, paletas ou arquivos.


## Melhorias v0.2.3 — zoom/pan e botões legíveis

### Zoom e navegação nas etapas 3 e 4
- roda do mouse: zoom;
- `+` / `−`: aumentar ou diminuir zoom;
- `Ajustar`: retornar à imagem inteira;
- botão do meio + arrastar: mover a imagem ampliada;
- `Shift + botão esquerdo` + arrastar: alternativa para mover;
- o nível de zoom aparece no canvas;
- máscaras e seleção continuam usando as coordenadas reais da imagem.

### Botões
Os nomes visíveis foram encurtados para evitar corte na barra de ferramentas.
Os principais controles agora possuem tooltip com a descrição completa ao passar o mouse.


## Mudanças v0.2.4 — revisão de UX da etapa de paletas

### Etapa combinada
As antigas etapas:
- `3. Áreas e paletas`
- `4. Cores essenciais`

foram reunidas em uma única etapa:

`3. Áreas, paletas e cores essenciais`

A seleção continua sendo feita por área, mas a revisão das essenciais passa a acontecer
na mesma tela.

### Cores essenciais consolidadas
Foi criada uma seção no topo do painel direito com:
- todos os RGBs essenciais únicos juntos;
- áreas de origem de cada RGB;
- ordenação visual para aproximar tons semelhantes;
- indicação da cor essencial mais próxima e distância ΔE;
- destaque para cores muito parecidas;
- botão `Remover` que elimina aquele RGB do conjunto essencial em todas as áreas.

A intenção é facilitar a identificação de redundâncias, por exemplo dois tons de preto
quase iguais selecionados em regiões diferentes.

### Zoom e pan
O modelo de câmera foi refeito:
- a roda do mouse aplica zoom sobre a posição do cursor;
- o ponto apontado pelo cursor permanece aproximadamente no mesmo lugar durante o zoom;
- botão do meio + arrastar move a imagem ampliada;
- Shift + botão esquerdo + arrastar faz a mesma navegação;
- `Ajustar` retorna à imagem inteira;
- zoom e pan não alteram coordenadas das máscaras.

### Menu lateral recolhível
O menu lateral pode ser recolhido pelo botão `☰` no cabeçalho.
- aberto: mostra nomes completos das etapas;
- recolhido: ocupa apenas uma faixa estreita e mostra os números;
- o nome completo da etapa permanece disponível por tooltip.

O objetivo é liberar espaço para imagem e paletas durante as etapas visuais.

## Fluxo atualizado
1. Imagem
2. Pixel Art IA
3. Áreas, paletas e cores essenciais
4. Matriz 100×100
5. Simplificação 50 cores
6. Edição manual
7. Molde e legenda
8. Exportar


## Ajuste v0.2.5 — foco visual da etapa 3

A avaliação da v0.2.4 mostrou que, mesmo com o menu lateral recolhível, a região superior
ainda consumia altura demais e reduzia a imagem — que é o foco principal desta etapa.

A v0.2.5 aproxima o layout da referência aprovada do antigo Palette Selector:

- cabeçalho da etapa reduzido;
- descrição curta;
- controles reunidos em uma única barra compacta;
- exportações movidas para o cabeçalho do painel de paletas;
- instruções extensas removidas da área principal e preservadas em tooltips;
- área central dividida praticamente em 50% imagem / 50% paletas;
- imagem passa a ocupar quase toda a altura útil disponível;
- título e contador da imagem foram compactados.

Objetivo visual:
`IMAGEM + SELEÇÃO | PALETAS + ESSENCIAIS`

A imagem deve permanecer grande o suficiente para seleção de áreas, deixando o zoom como
recurso de precisão, e não como compensação por um preview pequeno.


## v0.3 — Matriz lógica 100×100

A etapa 4 deixou de ser placeholder.

### Conversão
A Pixel Art aprovada é dividida geometricamente em uma arquitetura real de:

- 100 colunas;
- 100 linhas;
- 10.000 células.

Para cada célula:
1. são analisados somente os pixels da região correspondente da imagem original;
2. é calculada a mediana local apenas como referência;
3. o programa escolhe o RGB real da própria região mais próximo dessa mediana;
4. esse RGB real é usado como cor sólida da célula.

Consequências:
- não há interpolação;
- a matriz não inventa uma cor média;
- uma célula sempre possui um único RGB sólido;
- a simplificação de cores ainda NÃO acontece nesta etapa.

### Interface
A tela apresenta lado a lado:
- Pixel Art aprovada;
- Matriz 100×100.

Também oferece:
- gerar/regerar matriz;
- grade visual opcional;
- salvar PNG técnico 100×100;
- salvar preview ampliado 800×800.

A grade é apenas visual e não é salva dentro da matriz técnica.

### Persistência
A matriz 100×100 também é salva dentro do `.pixelart.json` como PNG compactado/base64,
permitindo fechar e reabrir o projeto mesmo sem exportar manualmente a matriz.


## v0.4 — Simplificação padrão para 50 cores

A etapa 5 deixou de ser placeholder.

### Construção da paleta final
1. Todos os RGBs essenciais únicos entram primeiro e permanecem exatos.
2. Se houver menos de 50 essenciais, as vagas restantes são preenchidas com RGBs reais
   presentes na matriz 100×100.
3. As cores complementares são escolhidas em espaço Lab por amostragem de maior distância,
   com um peso moderado para frequência. Isso evita preencher a paleta apenas com tons
   frequentes e quase iguais.

### Remapeamento
- a geometria 100×100 permanece idêntica;
- cada célula é mapeada para a cor final mais próxima em Lab;
- não há dithering;
- não existe deslocamento ou interpolação de células.

### Proteção efetiva das essenciais
Uma cor essencial precisa aparecer na imagem final, não apenas constar na paleta.

Se um RGB essencial exato não tiver sobrevivido naturalmente à matriz 100×100:
- o sistema localiza a área original onde a cor foi marcada;
- projeta essa região para a matriz 100×100;
- escolhe nessa região a célula mais próxima da cor essencial;
- aplica ali o RGB essencial exato.

### Validação
A tela apresenta:
- matriz 100×100 antes da simplificação;
- versão final de 50 cores;
- paleta final com as essenciais marcadas por estrela;
- contador de essenciais presentes.

A etapa só pode ser aprovada quando:
- a imagem possui exatamente 50 RGBs finais;
- todas as cores essenciais únicas estão presentes.


## v0.5 — Editor manual integrado

A etapa 6 deixa de ser placeholder e incorpora a lógica aprovada no
`pixel_art_manual_editor_v0_1_4`.

### Entrada automática
O editor recebe diretamente a matriz simplificada 100×100 da etapa anterior.
Não é necessário exportar e reabrir PNG ou JSON.

### Edição
- clique esquerdo pinta a célula lógica inteira;
- arrastar pinta várias células;
- clique direito funciona como conta-gotas;
- desfazer/refazer;
- grade visual opcional;
- hover sobre uma cor da paleta destaca todas as células daquele RGB.

### Paleta permitida
O editor aceita somente os 50 RGBs finais.

- cores essenciais mantêm os nomes das áreas onde foram selecionadas;
- cores complementares aparecem em `Outras cores da paleta final`;
- `★` identifica uma cor essencial.

### Persistência e exportações
A matriz editada é salva dentro do `.pixelart.json` e pode ser exportada como:
- PNG técnico real 100×100;
- preview ampliado 800×800;
- versão ampliada com grade.

### Correção técnica
A assinatura da simplificação passou a usar SHA-256 estável.
A v0.4 usava `hash()` do Python, que varia entre execuções e poderia invalidar
a simplificação depois de fechar e reabrir o aplicativo.
Resultados completos salvos na v0.4 são migrados automaticamente.


## v0.5.1 — Zoom na seleção de áreas e na edição manual

### Seleção de áreas
O zoom/pan da etapa 3 passa a ser considerado comportamento oficial:
- roda do mouse: zoom ancorado no cursor;
- `+` / `−`: alterar zoom;
- `Ajustar`: retornar à imagem inteira;
- botão do meio + arrastar: mover;
- `Shift + botão esquerdo` + arrastar: mover.

### Edição manual
A etapa 6 recebeu o mesmo modelo de navegação:
- roda do mouse: zoom na região apontada;
- `+` / `−`: aumentar/diminuir;
- `Ajustar`: voltar à matriz inteira;
- botão do meio + arrastar: pan;
- `Shift + botão esquerdo` + arrastar: pan alternativo.

O mapeamento continua sendo feito para a célula lógica real 100×100, então zoom e pan
não alteram qual célula é editada. O nível atual de zoom aparece no canvas e na barra de status.


## v0.5.2 — Paleta simplificada ordenada e remoção manual de cores próximas

Na etapa 5, a paleta final agora é exibida com **cores visualmente parecidas próximas entre si**.

### Novidades
- a paleta final passou a usar uma ordenação por similaridade para facilitar comparação visual;
- cores **essenciais** continuam protegidas;
- cores **complementares** podem ser marcadas para remoção diretamente na paleta;
- após marcar cores muito próximas, o botão **"Remover selecionadas e recriar"** monta uma nova paleta de 50 cores;
- a nova paleta mantém as essenciais e completa as vagas buscando cores mais distintas da matriz 100×100.

### Objetivo
Reduzir redundância cromática na simplificação final sem alterar a estrutura da pixel art.


## v0.5.3 — Correção da exibição da paleta simplificada

A v0.5.2 podia gerar a imagem simplificada corretamente, mas falhar ao montar os cartões da paleta, deixando a interface com `0 cores finais`.

### Correções
- o componente visual da paleta foi refeito usando botões Qt nativos mais robustos;
- a paleta continua ordenada por similaridade visual;
- cores complementares continuam selecionáveis para remoção;
- cores essenciais continuam protegidas;
- a recriação da paleta agora **bloqueia** as cores removidas para impedir que elas sejam escolhidas novamente logo em seguida;
- um erro de interface da paleta agora gera mensagem explícita, em vez de deixar a etapa parcialmente atualizada.


## v0.6 — Molde e legenda integrados

A etapa 7 deixou de ser placeholder e incorpora o comportamento aprovado no
`pixel_art_pattern_generator_v0_1`.

### Entrada automática
A etapa usa automaticamente:
- a matriz editada 100×100, quando houver edição manual válida;
- caso contrário, a matriz simplificada de 50 cores.

### Geração
O botão `Gerar molde + legenda` cria:
- códigos por cor no padrão `A…Z, Aa, Ab…`;
- código dentro de cada uma das 10.000 células;
- grade visual;
- numeração das colunas de 1 a 100;
- numeração das linhas de 1 a 100;
- legenda com amostra de cor, código, HEX, RGB, quantidade de células e percentual.

### Interface
A tela mostra:
- preview do molde à esquerda;
- tabela completa da legenda à direita.

### Exportações da etapa
- PNG do molde codificado;
- PNG da legenda;
- JSON da legenda;
- CSV da legenda;
- TXT da legenda.

O resultado é vinculado à assinatura da matriz final. Se a edição manual ou a
simplificação mudar, o molde anterior é invalidado automaticamente.


## v0.7 — Central de exportação

A etapa 8 deixou de ser placeholder e passa a reunir os arquivos finais do projeto em uma única tela.

### Arquivos disponíveis
- matriz técnica real 100×100;
- preview ampliado 800×800;
- imagem ampliada com grade visual;
- molde com códigos;
- legenda PNG;
- legenda JSON;
- legenda CSV;
- legenda TXT;
- manifesto JSON da exportação.

### Fluxo
1. Escolha uma pasta de destino.
2. Marque apenas os arquivos desejados ou use `Exportar tudo`.
3. O sistema usa automaticamente a matriz final mais recente:
   - edição manual, quando válida;
   - caso contrário, simplificação de 50 cores.
4. Molde e legenda são regenerados a partir dessa mesma matriz para evitar divergências.
5. Um manifesto registra os arquivos produzidos.

A exportação final só é considerada válida enquanto a matriz de origem permanecer a mesma.


## v0.7.1 — Remoção de cores sem repor a paleta

A etapa 5 foi ajustada conforme o fluxo desejado de revisão manual da paleta simplificada.

### Mudança principal
Quando a usuária marca cores complementares para descarte, o sistema **não completa a paleta de volta para 50 cores**.

Em vez disso:
- remove as cores complementares marcadas;
- preserva todas as essenciais;
- recria a imagem simplificada usando **somente as cores restantes**;
- permite que o resultado final tenha **qualquer quantidade entre 1 e 50 cores**.

### Ajustes adicionais
- botão da etapa 5 renomeado para deixar o comportamento mais claro;
- textos da interface atualizados para refletir que a paleta pode ficar com menos de 50 cores;
- regra de aprovação da etapa 5 alterada para aceitar resultados com **até 50 cores**, desde que todas as essenciais continuem presentes;
- etapas posteriores passam a tratar a origem como `simplificação final`, em vez de assumir exatamente 50 cores.
