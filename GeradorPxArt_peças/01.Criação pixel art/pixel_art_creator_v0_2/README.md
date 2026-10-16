# Pixel Art Creator — v0.2

Versão interativa do projeto de conversão de imagens para matriz 50×50.

## O que já funciona
- abertura de PNG/JPG/JPEG/WEBP;
- enquadramento quadrado 1:1;
- três métodos 50×50: Fidelidade, Detalhes e Pixel Art;
- escolha e checkpoint da versão-base;
- simplificação de cores por clustering perceptual em CIELAB/Lab;
- estratégias Equilibrada, Cores dominantes e Detalhes/cores raras;
- comparação ANTES × DEPOIS;
- clique em uma célula para identificar RGB/HEX e frequência;
- 🔒 cor travada: preserva exatamente o RGB e ocupa uma vaga da paleta;
- ⭐ cor prioritária: recebe peso extra no clustering;
- validação quando há mais cores travadas do que o limite solicitado;
- checkpoint obrigatório após aprovação da simplificação.

## Instalação
No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Se a v0.1 já estiver instalada em outro diretório, esta v0.2 tem novas dependências (`scikit-learn` e `scikit-image`), então execute novamente o `pip install -r requirements.txt` usando o ambiente desta pasta.

## Próxima etapa planejada
v0.3: códigos A…Z/Aa…, legenda visual, RGB/HEX, contagem e porcentagem de células, checkpoint da paleta.
