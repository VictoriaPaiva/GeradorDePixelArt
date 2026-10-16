
# Pixel Art Palette Selector v0.6

## Novidades

### Cores essenciais sobem para o topo

Ao selecionar uma cor, ela deixa a lista normal e aparece imediatamente em:

`★ CORES ESSENCIAIS`

logo abaixo do título da área.

Ao desmarcar, ela volta à lista normal.

### Seleção diretamente pela imagem

Ative:

`Selecionar cor pela imagem`

O pincel de regiões é temporariamente desativado.

Depois, clique em qualquer pixel que esteja dentro de uma área já criada.

O programa:

1. identifica a área;
2. lê o RGB original daquele pixel;
3. encontra perceptualmente a cor/grupo mais próximo na paleta daquela área;
4. marca ou desmarca essa cor como essencial;
5. destaca visualmente a cor escolhida.

Se áreas estiverem sobrepostas, a área criada mais recentemente tem prioridade.

### Contadores

Cada área mostra:

`Selecionadas: X`

A barra superior mostra:

`Essenciais totais: X`

O total é a soma das seleções de todas as áreas.

### Funcionalidades mantidas

- áreas nomeadas;
- hover do título destacando a área;
- hover da cor destacando pixels;
- paletas recolhíveis;
- excluir paleta sem excluir a área;
- excluir área;
- recalcular paleta;
- exportar JSON;
- exportar CSV;
- exportar TXT.

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
