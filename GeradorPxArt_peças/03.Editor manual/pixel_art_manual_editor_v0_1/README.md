
# Pixel Art Manual Editor v0.1

Editor para a etapa posterior à simplificação da Pixel Art.

## Uso recomendado neste projeto

1. Abra `cachorro_100x100_paleta_50.png`.
2. Carregue `cores_essenciais.v0_6.json`.
3. Escolha uma das 50 cores.
4. Clique ou arraste sobre células que deseja corrigir.
5. Botão direito sobre um pixel = conta-gotas.
6. Use Desfazer/Refazer quando necessário.
7. Ative/desative a grade.
8. Salve a matriz final PNG.

## Objetivo

Permitir correções locais sem alterar:

- escala 100×100;
- uma cor sólida por célula;
- paleta autorizada;
- estrutura da imagem inteira.

É especialmente útil para:
- quebrar blocos grandes de cor;
- restaurar highlights de olhos;
- corrigir bordas;
- ajustar pequenas sombras;
- inserir uma segunda nuance em uma região achatada.

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
