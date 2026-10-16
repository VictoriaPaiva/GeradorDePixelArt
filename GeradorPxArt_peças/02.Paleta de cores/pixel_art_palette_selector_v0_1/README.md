
# Pixel Art Palette Selector v0.1

Aplicação desktop em Python + PySide6 para:

- abrir uma imagem;
- calcular as 200 cores RGB exatas mais frequentes;
- mostrar a imagem ao lado da paleta;
- exibir código, HEX, RGB, quantidade de pixels e porcentagem;
- selecionar/deselecionar cores essenciais clicando nos cartões;
- destacar na imagem onde a cor ativa aparece;
- exportar as cores selecionadas em JSON e CSV.

## Instalação no Windows / PowerShell

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

## Uso

1. Clique em **Abrir imagem**.
2. A aplicação calcula automaticamente as 200 cores exatas mais frequentes.
3. Clique em um cartão de cor para marcar/desmarcar como **essencial**.
4. Dê duplo clique em um cartão para tornar aquela cor a cor ativa de destaque.
5. Use **Destacar cor ativa** para ver onde a cor aparece na imagem.
6. Use **Limpar destaque** para voltar à imagem normal.
7. Exporte as selecionadas em **JSON** ou **CSV**.

## Observação importante

Nesta etapa não há simplificação ou agrupamento cromático.
As cores mostradas são RGBs exatos presentes na imagem, ordenados por frequência.
