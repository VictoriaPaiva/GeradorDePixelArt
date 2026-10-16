# Guia de Ponto Cruz — v0.9.4

Aplicação desktop em PySide6 para transformar uma base artística criada no ChatGPT em um gráfico técnico de bordado em ponto cruz.

## Mudança principal da v0.9.3

A versão corrige a arquitetura híbrida: **a criação artística da matriz 50×50 / 100×100 deixa de ser responsabilidade principal do sistema local**.

O fluxo recomendado passa a ser:

1. importar a base artística inicial;
2. usar um **segundo prompt sistêmico** para pedir ao ChatGPT que redesenhe essa base pensando especificamente na matriz desejada;
3. importar a matriz artística aprovada;
4. o app faz apenas uma **normalização técnica** para a grade exata;
5. analisar paleta, editar, gerar gráfico, legenda e exportar.

## Fluxo v0.9.3

1. **Base artística + prompt inicial**
2. **Matriz artística via Chat**
3. **Normalização técnica**
4. **Cores essenciais (opcional)**
5. **Paleta técnica**
6. **Edição manual**
7. **Gráfico e legenda**
8. **Exportação**

## Etapa 2 — Matriz artística via Chat

O sistema agora monta um prompt específico para:
- matriz 50×50, 75×75, 100×100 ou personalizada entre 50 e 100;
- limite de cores entre 8 e 50;
- com ou sem contorno;
- preservação explícita de olhos, brilho natural dos olhos, expressão, nariz/focinho, boca/língua e acessórios.

A imagem criada no ChatGPT é importada novamente no aplicativo antes da grade técnica.

## Etapa 3 — Normalização técnica

### Preservação máxima — padrão
O sistema usa `nearest-neighbor` apenas para normalizar a imagem já desenhada para a quantidade exata de células.

Ele **não usa média nem mediana local** e não tenta redesenhar artisticamente olhos/focinho.

### Conversão automática experimental
O método antigo baseado em um RGB real próximo da mediana local continua disponível apenas para comparação/testes.

## Etapa 5 — Paleta técnica

Se a matriz já criada via Chat estiver dentro do limite de cores, use **Usar paleta atual**. Isso preserva a matriz sem remapear todas as células.

A **Simplificação local experimental** permanece disponível somente quando a imagem ainda ultrapassar o limite de cores.

## Instalação — Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python main.py
```

## Instalação — PowerShell

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Segurança

Não suba `.env`, chaves, tokens, credenciais, arquivos privados ou `.venv` para o GitHub.

## Status

**v0.9.4 executável — aguardando avaliação da grade e legenda final.**

## v0.9.4 — Grade e legenda final

A etapa 7 foi concluída para gerar o material técnico de bordado a partir da matriz final aprovada.

### Saídas da etapa 7
- grade colorida com códigos em cada célula;
- grade para impressão em fundo branco com os mesmos códigos;
- linhas finas a cada ponto e linhas reforçadas a cada 10 pontos;
- coordenadas a cada 5 pontos;
- legenda visual com código, amostra da cor, HEX, RGB, quantidade de pontos e percentual;
- exportação da legenda em PNG, JSON, CSV e TXT.

Os códigos seguem o padrão `C01`, `C02`, `C03`... para facilitar a leitura e a conferência do gráfico.

A etapa usa automaticamente a fonte final mais recente, nesta prioridade:
1. edição manual válida;
2. paleta técnica/simplificação aprovada;
3. matriz técnica, quando disponível.

A central de exportação também passa a salvar separadamente:
- gráfico colorido;
- gráfico para impressão com códigos;
- legenda e arquivos técnicos.
