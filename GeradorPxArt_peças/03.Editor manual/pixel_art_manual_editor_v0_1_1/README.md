
# Pixel Art Manual Editor v0.1.1

## Correção principal

Agora o clique pinta a **célula inteira da grade lógica**, e não apenas um ponto isolado.

Isso significa que:

- se você abrir uma matriz real `100x100`, cada clique pinta 1 célula inteira;
- se você abrir uma imagem ampliada (por exemplo um preview `800x800`), o editor pode interpretar essa imagem como uma grade lógica `100x100` e pintar o **bloco inteiro correspondente**.

## Nova opção: Grade lógica

No topo da aplicação, você pode escolher:

- `Grade lógica: Auto`
- `Grade lógica: 50x50`
- `Grade lógica: 100x100`
- `Grade lógica: Pixels reais`

### Recomendação para este projeto

Use:

- `100x100` para imagens finais do sistema;
- `50x50` apenas em testes antigos;
- `Auto` na maioria dos casos.

## Comportamento do clique

- Botão esquerdo: pinta a célula inteira
- Arrastar com botão esquerdo: pinta várias células inteiras
- Botão direito: conta-gotas

## Instalação

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
