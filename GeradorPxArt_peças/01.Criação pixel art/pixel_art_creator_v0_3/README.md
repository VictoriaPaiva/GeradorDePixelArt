# Pixel Art Creator — v0.3

Esta versão concentra-se na qualidade artística e no controle da simplificação.

## Novidades

- **3 interpretações 50×50**:
  - Fidelidade: redução fotográfica de referência.
  - Ilustrada: remove microtextura e cria massas de cor mais desenhadas.
  - Pixel Art artística: simplificação mais forte, paleta gráfica preliminar e reforço de contornos.
- **Editor opcional de regiões** antes da simplificação.
  - Pincel clicável/arrastável (1–9 células).
  - Normal/apagar.
  - Preservar detalhes.
  - Simplificar.
  - Simplificar muito.
- **Textura controlada por região** com 2 ou 3 tons.
  - Usa somente cores que já pertencem à paleta final.
  - A distribuição claro/escuro consulta a luminosidade da imagem antes da simplificação, evitando um xadrez aleatório.
  - Só é aplicada em blocos contínuos suficientemente grandes, para reduzir o efeito de manchas chapadas.
- Cores travadas e prioritárias da v0.2 continuam disponíveis.
- Checkpoint das máscaras de região.

> A máscara colorida do editor é apenas uma visualização. Ela nunca altera os RGBs da pixel art.

## Instalação no Windows / PowerShell

Na pasta do projeto:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Se preferir não ativar o ambiente:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

## Fluxo atual

1. Abrir imagem.
2. Aprovar enquadramento 1:1.
3. Comparar Fidelidade / Ilustrada / Pixel Art artística.
4. Aprovar uma versão.
5. Opcionalmente pintar regiões e definir preservação, simplificação e textura.
6. Definir número de cores, travar/priorizar cores e calcular a paleta.
7. Aprovar a simplificação.

## Observação sobre a v0.3

A interpretação artística é algorítmica, não generativa. Portanto ela procura aproximar a linguagem visual do exemplo desenhado por meio de segmentação cromática, remoção de microdetalhes e contornos, mas não "redesenha" semanticamente objetos como um modelo de geração de imagens faria. O objetivo desta versão é termos uma base determinística e editável para calibrar com fotos reais.
