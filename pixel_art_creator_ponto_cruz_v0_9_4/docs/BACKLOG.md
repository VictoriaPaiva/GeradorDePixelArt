# BACKLOG — Guia de Ponto Cruz v0.9.3

## Status geral
Versão executável preparada para avaliação.

## Concluído nesta versão
- [x] Separar criação artística da matriz da normalização técnica.
- [x] Criar etapa **Matriz artística via Chat**.
- [x] Criar prompt específico por matriz, cores e contorno.
- [x] Importar o resultado artístico do Chat antes da grade técnica.
- [x] Tornar **Preservação máxima** o modo padrão da normalização.
- [x] Manter método antigo apenas como conversão automática experimental.
- [x] Adicionar **Usar paleta atual** para evitar simplificação quando a matriz já estiver dentro do limite.
- [x] Marcar a simplificação automática local como experimental.
- [x] Remover a etapa antiga de enquadramento automático do fluxo principal.

## Próxima avaliação
- [ ] Testar matriz artística 50×50 gerada no Chat e comparar expressão/olhos com v0.9/v0.9.2.
- [ ] Testar matriz artística 100×100.
- [ ] Conferir se a normalização nearest-neighbor preserva os focos melhor que o método antigo.
- [ ] Conferir quantas cores únicas restam após a normalização.
- [ ] Avaliar necessidade de melhorar ainda mais a leitura técnica de blocos da imagem gerada pelo Chat.

## Próximos refinamentos possíveis
- [ ] Detector de regiões focais (olhos/nariz/boca) para auditoria, não para redesenho.
- [ ] Aviso automático quando a paleta ultrapassar o limite selecionado.
- [ ] Comparador lado a lado: matriz artística Chat × grade técnica.
- [ ] Relatório de mudança de cores após qualquer simplificação local.
- [ ] Mapeamento opcional para linhas DMC/Anchor.
- [ ] PDF final para impressão.

## v0.9.4 — Grade e legenda final

### PAT-002 — Grade técnica completa
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.9.4  
**Implementação:** geração de duas saídas: grade colorida com códigos e grade em fundo branco para impressão. Linhas reforçadas a cada 10 pontos e coordenadas a cada 5 pontos.

### PAT-003 — Códigos estáveis por cor
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.9.4  
**Implementação:** códigos `C01`, `C02`, ... ordenados por frequência de uso da cor na matriz.

### PAT-004 — Legenda consolidada
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.9.4  
**Implementação:** legenda com amostra visual, código, HEX, RGB, quantidade de pontos e percentual; exportações PNG/JSON/CSV/TXT.

### EXP-005 — Exportar duas grades
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.9.4  
**Implementação:** a central de exportação passa a gerar separadamente o gráfico colorido e o gráfico para impressão com códigos.

## Ponto de retomada — v0.9.4
**Última atividade:** implementação da etapa final de grade e legenda.  
**Próxima ação:** testar visualmente grade 50×50 e 100×100 no Windows e validar legibilidade dos códigos e da legenda.  
**Depois da aprovação:** considerar o fluxo principal do gerador de guia de ponto cruz completo e seguir apenas com refinamentos de impressão/PDF/DMC.
