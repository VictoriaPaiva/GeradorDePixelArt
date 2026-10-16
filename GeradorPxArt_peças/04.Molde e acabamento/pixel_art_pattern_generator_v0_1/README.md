
# Pixel Art Pattern Generator v0.1

Etapa seguinte do sistema de criação de Pixel Art.

## Entrada recomendada

Imagem final já aprovada e editada:

- matriz 100x100;
- aproximadamente 50 cores;
- uma única cor sólida por célula.

## O programa gera

### Legenda

Cada RGB usado na imagem recebe um código:

- A até Z
- depois Aa, Ab, Ac...
- depois Ba, Bb...

A legenda contém:

- código;
- amostra da cor;
- HEX;
- RGB;
- número de células;
- porcentagem da imagem.

### Molde

Gera imagem com:

- grade;
- código dentro de cada célula;
- colunas numeradas no topo;
- linhas numeradas na lateral.

### Exportações

- PNG do molde;
- PNG da legenda;
- JSON;
- CSV;
- TXT.

## Fluxo oficial atual do projeto

1. Pixel Art artística aprovada
2. Escala 100x100
3. Seleção de cores essenciais
4. Simplificação para 50 cores
5. Edição manual por pixel
6. Exportação limpa / com grade
7. Legenda + códigos + molde  ← esta aplicação

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
