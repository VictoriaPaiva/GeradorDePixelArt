
# Pixel Art Palette Selector v0.2

Esta versão substitui o ranking simples de RGBs exatos por uma paleta de
**cores predominantes após agrupar nuances muito similares**.

## O que mudou

- Conta os RGBs presentes na imagem.
- Converte uma ampla seleção de cores para o espaço perceptual Lab.
- Agrupa apenas cores próximas usando uma tolerância configurável.
- Soma a frequência das nuances agrupadas.
- Mostra os **200 grupos mais predominantes**.
- A cor visível no cartão é sempre um RGB real presente na imagem.
- Mantém cores saturadas no conjunto de candidatos para reduzir o risco de
  detalhes vivos, como azul ou rosa, desaparecerem.
- Cada cartão informa quantas nuances foram agrupadas.
- Clique para selecionar cores essenciais.
- Duplo clique para destacar aproximadamente aquela família cromática na imagem.
- Exporta a seleção em JSON ou CSV.

## Controle de agrupamento

A interface possui o controle **Agrupamento de similares**.

- `1.0–2.5`: muito conservador; funde apenas cores quase idênticas.
- `3.0–4.5`: recomendado para pixel art.
- `5.0–8.0`: agrupamento progressivamente mais agressivo.

O padrão é `4.0`.

## Instalação no Windows / PowerShell

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Importante

Esta aplicação NÃO modifica a imagem e NÃO reduz a imagem para 200 cores.
Ela só constrói uma legenda para seleção das cores/famílias que deverão ser
preservadas nas etapas posteriores do projeto.
