
# Pixel Art Palette Selector v0.4 — Áreas nomeadas + hover inspector

## Novidades

### 1. Áreas persistentes e nomeadas

Depois de pintar uma região, clique:

`Criar área + gerar paleta`

A aplicação sugere:

- Área selecionada 1
- Área selecionada 2
- Área selecionada 3

Você pode aceitar esse nome ou escrever outro, como:

- Língua
- Coleira
- Olhos
- Fundo
- Pelo claro

Cada área mantém:

- sua máscara;
- sua própria paleta;
- suas cores essenciais selecionadas.

### 2. Paleta abaixo do título da área

As cores de cada região ficam agrupadas visualmente em uma seção:

`Área selecionada 1`
→ paleta dessa área

`Área selecionada 2`
→ paleta dessa área

etc.

### 3. Hover tipo "Inspecionar"

Passe o mouse sobre o título de uma área.

A região correspondente fica destacada em amarelo na imagem, semelhante ao
comportamento do inspetor de elementos de navegadores.

Ao tirar o mouse do título, o destaque some.

### 4. Cores essenciais por área

Cada cartão pode ser marcado como essencial.

As escolhas ficam salvas dentro da própria área.

O botão:

`Exportar todas as cores essenciais`

gera um JSON contendo:

- nome da área;
- código;
- HEX;
- RGB;
- frequência naquela área;
- quantidade de nuances agrupadas.

## Máscaras

- Magenta = seleção atual ainda não salva.
- Azul-claro = áreas já salvas.
- Amarelo = área cujo título está sob o mouse.

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
