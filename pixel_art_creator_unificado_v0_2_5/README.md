# Pixel Art Creator — Sistema Unificado v0.2.5

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
