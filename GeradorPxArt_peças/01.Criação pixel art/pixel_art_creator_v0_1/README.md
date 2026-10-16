# Pixel Art Creator — v0.1

Primeira versão executável do projeto aprovado.

## O que já faz
- Abre PNG, JPG/JPEG e WEBP.
- Permite enquadramento quadrado 1:1 com posição e tamanho ajustáveis.
- Exige aprovação do enquadramento.
- Gera 3 matrizes lógicas de 50×50, cada célula com um único RGB:
  1. Fidelidade — amostragem por área (BOX).
  2. Detalhes — preservação de bordas com unsharp + redução de alta qualidade.
  3. Pixel Art — contraste/cor + limpeza mediana antes da redução.
- Mostra as 3 versões lado a lado sem suavização na ampliação.
- Permite escolher e aprovar uma versão.
- Mantém checkpoints da imagem original, recorte e pixel art aprovada em memória.

## Instalação
Recomendado: Python 3.11 ou 3.12.

No terminal, dentro desta pasta:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Depois:
```bash
pip install -r requirements.txt
python main.py
```

## Limites intencionais da v0.1
Esta versão termina após a aprovação de uma das três pixel arts. A v0.2 adicionará:
- escolha do número de cores;
- quantização perceptual em Lab;
- comparação antes/depois;
- cores travadas e prioritárias;
- aprovação/refação da simplificação;
- persistência dos checkpoints em arquivo de projeto.

As letras, grade, legenda, coordenadas e exportações finais entram nas versões seguintes.
