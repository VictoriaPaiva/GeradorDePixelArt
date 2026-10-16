
# Pixel Art Palette Selector v0.5

## Novidades

### Seleção desaparece após salvar a área

A máscara magenta aparece somente enquanto você está desenhando uma nova área.

Depois de clicar:

`Criar área + gerar paleta`

o magenta some e a imagem volta a mostrar suas cores originais.

### Hover sobre cores da paleta

Passe o mouse por cima de um cartão RGB.

Os pixels daquela família cromática, dentro da área correspondente, recebem
um destaque ciano na imagem.

Assim você consegue ver onde aquela cor aparece antes de marcar como essencial.

### Hover sobre o título da área

Ao passar o mouse sobre:

`Área selecionada 1`

a máscara da região correspondente aparece em amarelo, como um inspetor visual.

### Paletas recolhíveis

Cada área possui um botão:

- `▼` paleta aberta
- `▶` paleta recolhida

Isso facilita visualizar uma lista grande de regiões.

### Excluir paleta sem excluir área

`Excluir paleta`

remove apenas a paleta e as cores essenciais daquela área.

A máscara/região permanece salva.

Você pode clicar em:

`Recalcular paleta`

para gerar novamente.

### Excluir área

`Excluir área`

remove região, máscara, paleta e escolhas.

### Exportações

Os botões voltaram à barra superior:

- Exportar JSON
- Exportar CSV
- Exportar TXT

O TXT é organizado por área:

```text
CORES ESSENCIAIS POR ÁREA

[Língua]
A | #F25C73 | RGB(242, 92, 115)
B | #A7283F | RGB(167, 40, 63)

[Coleira]
A | #1795F0 | RGB(23, 149, 240)
```

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
