# Pixel Art Creator — Sistema Unificado v0.2

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
