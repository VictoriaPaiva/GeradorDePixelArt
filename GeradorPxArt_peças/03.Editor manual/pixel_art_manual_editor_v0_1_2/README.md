
# Pixel Art Manual Editor v0.1.2

## Novas melhorias

### 1. Paleta agrupada por títulos do JSON

Ao carregar o JSON, as cores aparecem separadas por grupos/títulos, por exemplo:

- Olhos
- Língua
- Coleira
- Fundo
- Pelo claro

Isso facilita encontrar rapidamente a cor dentro do contexto certo.

### 2. Hover nas cores da paleta

Ao passar o mouse por cima de uma cor na lista, todos os pixels/células da imagem
que correspondem exatamente àquela cor ficam destacados em amarelo.

Assim você consegue comparar como a cor aparece distribuída no desenho antes de usá-la.

## Funcionalidades mantidas

- clique pinta a célula inteira da grade lógica;
- grade lógica Auto / 50x50 / 100x100 / Pixels reais;
- botão direito como conta-gotas;
- desfazer / refazer;
- salvar PNG;
- salvar preview ampliado.

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
