# Pixel Art Creator v0.4

Esta versão revisa o motor que gera as três propostas 50×50.

## O que mudou

- **Fidelidade** continua deliberadamente fotográfica.
- **Ilustrada** agora usa segmentação em regiões coerentes, preservação de bordas e uma paleta com tons perceptualmente separados.
- **Pixel Art artística** foi reescrita para produzir planos de cor mais fortes, evitar longas escadas de RGB quase iguais e reforçar seletivamente limites estruturais.
- Foi adicionada **quebra de gradientes suaves**: longe de bordas importantes, tons quase iguais são incorporados a planos próximos em vez de formar transições borradas.
- A paleta preliminar usa **distância perceptual em Lab** para evitar gastar muitas cores com nuances quase indistinguíveis.
- As etapas da v0.3 continuam disponíveis: regiões de preservar/simplificar, textura 2/3 tons, cores travadas e prioritárias, e simplificação final.

## Instalação (Windows / PowerShell)

```powershell
cd "D:\Pixel Art\pixel_art_creator_v0_4"
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Teste recomendado

Use a mesma foto de teste da versão anterior. Compare principalmente:

1. região entre olhos e focinho;
2. contorno dos olhos e focinho;
3. pelo branco/bege;
4. gramado;
5. coleira azul.

O objetivo da v0.4 é que **Ilustrada** e **Pixel Art artística** não sejam apenas versões mais borradas de Fidelidade. A versão artística deve apresentar mudanças de cor mais deliberadas e planos mais legíveis.
