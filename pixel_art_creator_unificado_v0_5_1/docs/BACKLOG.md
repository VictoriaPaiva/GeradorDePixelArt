# BACKLOG — Pixel Art Creator Unificado

**Projeto:** Pixel Art Creator  
**Versão-base atual:** v0.5.1  
**Última atualização:** 13/10/2026  
**Responsáveis pelo planejamento/evolução:** Usuária + ChatGPT  

## Como usar este backlog

Este arquivo deve ser atualizado sempre que:
- surgir uma nova ideia relevante;
- uma funcionalidade mudar de escopo;
- uma atividade for iniciada, concluída, adiada ou cancelada;
- uma decisão de arquitetura alterar atividades futuras.

### Status utilizados

- `CONCLUÍDO` — implementado e aprovado.
- `AGUARDANDO AVALIAÇÃO` — implementado, mas ainda depende da validação da usuária.
- `EM ANDAMENTO` — desenvolvimento iniciado.
- `PLANEJADO` — definido para uma versão futura.
- `IDEIA / BACKLOG` — ideia válida, mas ainda sem versão definida.
- `BLOQUEADO` — depende de decisão, ferramenta ou etapa anterior.
- `CANCELADO` — removido do escopo.

---

## Visão resumida

| ID | Atividade | Status | Versão/etapa prevista |
|---|---|---|---|
| DOC-001 | Criar backlog oficial do projeto | CONCLUÍDO | Documentação |
| DOC-002 | Criar template central do projeto | CONCLUÍDO | Documentação |
| DOC-003 | Atualizar backlog e template ao longo da evolução | EM ANDAMENTO | Contínuo |
| CORE-001 | Criar estrutura inicial do sistema unificado | CONCLUÍDO | v0.1 |
| CORE-002 | Avaliar navegação, interface e checkpoints da v0.1 | CONCLUÍDO | v0.1 |
| PAL-001 | Integrar criação de áreas e levantamento de paletas | AGUARDANDO AVALIAÇÃO | v0.2 |
| PAL-002 | Integrar seleção de cores essenciais | AGUARDANDO AVALIAÇÃO | v0.2 |
| PAL-003 | Adicionar contador total bruto e contador de RGBs únicos | AGUARDANDO AVALIAÇÃO | v0.2 |
| PAL-004 | Exportar seleção de cores em JSON/TXT/CSV | AGUARDANDO AVALIAÇÃO | v0.2 |
| MAT-001 | Integrar enquadramento/matriz lógica 100×100 | CONCLUÍDO | v0.3 |
| SIM-001 | Integrar simplificação padrão para 50 cores | CONCLUÍDO | v0.4 |
| SIM-002 | Garantir proteção das cores essenciais | CONCLUÍDO | v0.4 |
| SIM-003 | Melhorar tratamento de grandes blocos sólidos de uma cor | IDEIA / BACKLOG | Refinamento |
| MAN-001 | Integrar editor manual aprovado v0.1.4 | CONCLUÍDO | v0.5 |
| UX-009 | Padronizar zoom/pan na seleção de áreas e edição manual | AGUARDANDO AVALIAÇÃO | v0.5.1 |
| PAT-001 | Integrar Pattern Generator aprovado v0.1 | PLANEJADO | Molde/acabamento |
| AI-001 | Integrar geração de Pixel Art via IA | PLANEJADO | Integração IA |
| AI-002 | Adicionar aprovação / recriação da imagem gerada por IA | PLANEJADO | Integração IA |
| SAVE-001 | Evoluir salvamento do projeto para pacote completo e portátil | PLANEJADO | Persistência |
| SAVE-002 | Adicionar checkpoints e recuperação do ponto de retomada | PLANEJADO | Persistência |
| EXP-001 | Centralizar exportações finais | PLANEJADO | Exportação |
| EXP-002 | Gerar PDF/molde pronto para impressão | IDEIA / BACKLOG | Futuro |
| UX-001 | Padronizar visual das etapas e indicadores de progresso | IDEIA / BACKLOG | Acabamento |
| UX-002 | Avisar antes de invalidar etapas posteriores | PLANEJADO | Núcleo |
| TEST-001 | Criar testes de regressão para funcionalidades migradas | PLANEJADO | Durante integração |
| BUG-001 | Corrigir corte visual no preview de imagens verticais | CONCLUÍDO | v0.2.1 |
| BUG-002 | Corrigir canvas oculto pelo rodapé nas etapas 3 e 4 | CONCLUÍDO | v0.2.2 |
| PAL-005 | Criar revisão consolidada das cores essenciais | AGUARDANDO AVALIAÇÃO | v0.2.4 |
| PAL-006 | Ordenar essenciais por proximidade visual e sinalizar tons redundantes | AGUARDANDO AVALIAÇÃO | v0.2.4 |
| UX-005 | Reunir paletas e essenciais na mesma etapa | AGUARDANDO AVALIAÇÃO | v0.2.4 |
| UX-006 | Tornar menu lateral recolhível | AGUARDANDO AVALIAÇÃO | v0.2.4 |
| UX-007 | Refazer zoom para ancorar no cursor e permitir pan real | AGUARDANDO AVALIAÇÃO | v0.2.4 |
| UX-008 | Compactar cabeçalho da etapa 3 e priorizar divisão 50/50 imagem/paleta | AGUARDANDO AVALIAÇÃO | v0.2.5 |

---

## Detalhamento das atividades

### DOC-001 — Criar backlog oficial do projeto
**Status:** CONCLUÍDO  
**Objetivo:** manter uma lista única de atividades presentes e futuras, com status e plano resumido.  
**Plano:** este arquivo passa a acompanhar a versão unificada e deve ser atualizado sempre que houver evolução relevante.

### DOC-002 — Criar template central do projeto
**Status:** CONCLUÍDO  
**Objetivo:** criar um documento de continuidade inspirado no `Template do projeto Spotify.docx`.  
**Plano:** manter resumo, objetivo, estado atual, decisões, problemas, próximos passos, histórico e ponto de retomada atualizados.

### DOC-003 — Atualização contínua da documentação
**Status:** EM ANDAMENTO  
**Objetivo:** evitar que código e documentação se afastem.  
**Plano:** após cada evolução relevante do sistema:
1. atualizar este backlog;
2. atualizar o template central do projeto;
3. registrar decisões importantes;
4. atualizar o ponto de retomada.

---

### CORE-001 — Estrutura inicial unificada
**Status:** CONCLUÍDO  
**Versão:** v0.1  
**O que foi implementado:**
- janela única;
- menu lateral com 9 etapas;
- navegação Voltar/Próximo;
- aprovação por etapa;
- bloqueio de avanço sem aprovação;
- carregamento da imagem inicial;
- importação temporária de Pixel Art já gerada;
- `ProjectState` central;
- abrir/salvar projeto em `.pixelart.json`;
- placeholders das etapas futuras.

### CORE-002 — Avaliação da v0.1
**Status:** CONCLUÍDO  
**Resultado:** estrutura da v0.1 aprovada pela usuária.  
**Avaliar principalmente:**
- organização das etapas;
- menu lateral;
- fluxo de aprovação;
- navegação;
- visual;
- entendimento geral da interface.

---

### PAL-001 — Áreas e levantamento de paletas
**Status:** AGUARDANDO AVALIAÇÃO  
**Referência:** `pixel_art_palette_selector_v0_6_1`  
**Plano:**
- reaproveitar máscara por região;
- nomear áreas;
- calcular paleta por área;
- agrupar cores similares;
- preservar representante RGB real;
- hover da área;
- hover da cor;
- recolher/expandir paletas;
- excluir/recalcular paleta;
- excluir área.

### PAL-002 — Seleção de cores essenciais
**Status:** AGUARDANDO AVALIAÇÃO  
**Plano:**
- seleção por cartão;
- seleção direta pela imagem;
- promover cores essenciais ao topo de cada área;
- preservar associação área ↔ cor;
- proteger essas cores na etapa de simplificação.

### PAL-003 — Contadores
**Status:** AGUARDANDO AVALIAÇÃO  
**Plano:**
- contador por área;
- total bruto de seleções;
- total de RGBs únicos;
- mesma cor selecionada em duas áreas conta uma única vez no total de RGBs únicos.

### PAL-004 — Exportação das cores essenciais
**Status:** AGUARDANDO AVALIAÇÃO  
**Plano:** JSON, TXT e CSV contendo área, código, HEX, RGB e demais metadados úteis.

---

### MAT-001 — Matriz lógica 100×100
**Status:** CONCLUÍDO
**Versão:** v0.3  
**Decisão oficial:** 100×100 é a escala padrão.  
**Plano:**
- 10.000 células;
- uma única cor sólida por célula;
- sem interpolação;
- evitar média;
- preferir cores reais da imagem;
- exibir checkpoint para aprovação.

---

### SIM-001 — Simplificação padrão para 50 cores
**Status:** CONCLUÍDO
**Versão:** v0.4  
**Decisão oficial:** 50 cores é o padrão; 35 cores perdeu qualidade nos testes.  
**Plano:**
- iniciar pelas cores essenciais;
- completar até 50 com cores relevantes da imagem;
- preservar famílias cromáticas e contraste;
- não alterar a geometria da Pixel Art;
- sem dithering aleatório.

### SIM-002 — Proteção de cores essenciais
**Status:** CONCLUÍDO
**Versão:** v0.4  
**Plano:** toda cor marcada como essencial precisa sobreviver à simplificação, salvo decisão manual explícita da usuária.

### SIM-003 — Tratamento de blocos sólidos
**Status:** IDEIA / BACKLOG  
**Problema:** grandes regiões 4-conectadas de uma mesma cor podem achatar volume e textura.  
**Plano futuro:** detectar componentes grandes e sugerir recuperação de nuances da própria paleta guiada pela imagem anterior à simplificação. A edição manual permanece como garantia final.

---

### MAN-001 — Integração do editor manual
**Status:** CONCLUÍDO
**Versão:** v0.5  
**Referência aprovada:** `pixel_art_manual_editor_v0_1_4`  
**Manter:**
- edição por célula inteira;
- grade lógica 100×100;
- conta-gotas;
- paleta agrupada por área;
- hover de cor;
- desfazer/refazer;
- salvar matriz técnica 100×100;
- preview ampliado;
- imagem com grade.

---

### PAT-001 — Integração do gerador de molde
**Status:** PLANEJADO  
**Referência aprovada:** `pixel_art_pattern_generator_v0_1`  
**Manter:**
- grade;
- códigos nas células;
- legenda;
- HEX/RGB;
- quantidade de células;
- porcentagem;
- numeração de linhas e colunas;
- JSON/CSV/TXT;
- PNG do molde e da legenda.

---

### AI-001 — Geração de Pixel Art via IA
**Status:** PLANEJADO  
**Plano:** criar serviço desacoplado da interface para permitir troca de modelo/API futuramente.  
**Resultado esperado:** Pixel Art artística antes da criação da matriz lógica.

### AI-002 — Validação da geração
**Status:** PLANEJADO  
**Plano:** permitir aprovar ou recriar a imagem antes de avançar.

---

### SAVE-001 — Projeto portátil
**Status:** PLANEJADO  
**Plano:** substituir gradualmente dependência de caminhos externos por uma pasta/pacote de projeto contendo estado e arquivos derivados.

### SAVE-002 — Checkpoints
**Status:** PLANEJADO  
**Plano:** registrar aprovações e ponto de retomada; permitir fechar e continuar posteriormente.

---

### EXP-001 — Central de exportação
**Status:** PLANEJADO  
**Plano:** reunir todas as saídas em uma única etapa final.

### EXP-002 — PDF para impressão
**Status:** IDEIA / BACKLOG  
**Plano:** gerar futuramente molde paginado e pronto para impressão, sem alterar a matriz técnica.

---

## Decisões que NÃO precisam ser rediscutidas neste momento

- escala lógica padrão: **100×100**;
- simplificação padrão: **50 cores**;
- cores essenciais são protegidas;
- sem dithering aleatório;
- evitar interpolação e média de cores;
- grade é camada visual e não integra a paleta;
- edição manual deve continuar disponível;
- validação/aprovação entre transformações visuais importantes;
- os módulos já aprovados devem ser reaproveitados, não reescritos sem motivo.

---

## Ponto atual de retomada

**Última atividade concluída:** ajuste do layout da etapa 3 na v0.2.5 para priorizar imagem e paletas.  
**Próxima ação:** avaliação da v0.2.5 pela usuária, principalmente do tamanho útil da imagem e da divisão 50/50.  
**Depois da aprovação:** integrar a matriz lógica 100×100.


### BUG-001 — Preview cortando imagem vertical
**Status:** CONCLUÍDO  
**Versão:** v0.2.1  
**Problema:** a imagem importada aparecia visualmente cortada na etapa de Pixel Art, embora o arquivo original estivesse íntegro.  
**Correção:** o preview passou a desenhar a imagem com `QPainter`, usando `KeepAspectRatio` e considerando largura e altura disponíveis.  
**Impacto:** somente visual; nenhum arquivo ou matriz era cortado de fato.


### BUG-002 — Canvas parcialmente oculto pelo rodapé
**Status:** CONCLUÍDO  
**Versão:** v0.2.2  
**Problema:** nas etapas 3 e 4, imagens verticais podiam parecer cortadas na parte inferior.  
**Causa:** o `MaskCanvas` possuía tamanho mínimo de 520×520 e podia ultrapassar a altura útil da página, ficando parcialmente escondido pelo rodapé.  
**Correção:** redução do mínimo do canvas e adoção de política de tamanho expansível, permitindo que ele se ajuste à altura realmente disponível sem perder a proporção da imagem.  
**Impacto:** somente layout; máscaras, pixels e paletas não eram cortados.


### UX-003 — Zoom e pan para seleção precisa
**Status:** CONCLUÍDO  
**Versão:** v0.2.3  
**Motivo:** a imagem inteira cabia no canvas, mas ficava pequena para selecionar regiões detalhadas.  
**Implementação:** zoom por roda do mouse/botões, pan por botão do meio ou Shift + arrastar e botão Ajustar.  
**Regra:** zoom e pan afetam somente a visualização; máscaras continuam ligadas às coordenadas reais da imagem.

### UX-004 — Botões legíveis
**Status:** CONCLUÍDO  
**Versão:** v0.2.3  
**Problema:** rótulos longos eram cortados.  
**Implementação:** nomes visíveis mais curtos + tooltips com a descrição completa.


### PAL-005 — Revisão consolidada das cores essenciais
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.2.4  
**Motivo:** cores selecionadas em áreas diferentes podem ser visualmente redundantes, mesmo possuindo RGBs distintos.  
**Implementação:** criação de um painel único com todos os RGBs essenciais, sem separação por área, mantendo apenas a informação de origem.  
**Ação disponível:** remover um RGB consolidado do conjunto essencial em todas as áreas onde ele estava marcado.

### PAL-006 — Organização por proximidade visual
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.2.4  
**Plano implementado:** organizar essenciais neutras por luminosidade e cores cromáticas por família/hue, aproximando tons parecidos.  
**Apoio visual:** cada cor mostra a essencial mais próxima e sua distância ΔE; valores muito baixos são destacados para ajudar a identificar redundâncias.  
**Objetivo futuro:** se essa abordagem for aprovada, ela poderá servir também como base para sugestões automáticas de fusão, sempre dependendo de confirmação da usuária.

### UX-005 — Unificar paletas e cores essenciais na mesma etapa
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.2.4  
**Decisão:** as etapas 3 e 4 anteriores foram fundidas.  
**Novo fluxo:** a usuária cria áreas, analisa as paletas, marca essenciais e revisa o conjunto consolidado sem trocar de página.

### UX-006 — Menu lateral recolhível
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.2.4  
**Motivo:** a navegação sequencial por Próximo/Voltar reduz a necessidade de um menu lateral permanentemente largo.  
**Implementação:** menu aberto com nomes completos e modo recolhido estreito com números + tooltips.  
**Objetivo:** liberar espaço horizontal para imagem e paletas sem perder acesso direto às etapas.

### UX-007 — Zoom ancorado no cursor e pan real
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.2.4  
**Problema anterior:** o zoom era percebido como centrado e a navegação pela área ampliada não era útil o suficiente.  
**Implementação:** novo modelo de câmera baseado em coordenada central da imagem; zoom pela roda mantém o ponto sob o cursor e pan move a área visível.  
**Controles:** roda do mouse, +/−, Ajustar, botão do meio + arrastar ou Shift + botão esquerdo + arrastar.  
**Regra:** zoom/pan não alteram máscaras nem coordenadas reais da imagem.


### UX-008 — Priorizar imagem e paleta no layout da etapa 3
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.2.5  
**Feedback:** mesmo com menu lateral recolhível, o conjunto de título, descrição, controles e instruções ainda ocupava altura demais, deixando a imagem pequena.  
**Referência visual:** o antigo `pixel_art_palette_selector_v0_6`, cuja tela principal era dividida aproximadamente ao meio entre imagem e paleta.  
**Implementação:** cabeçalho reduzido, descrição curta, uma única barra compacta de controles, exportações no cabeçalho da paleta e remoção de instruções longas da área principal.  
**Objetivo:** manter imagem e paletas como os dois elementos dominantes da tela, cada um ocupando aproximadamente metade da largura e quase toda a altura útil.


### MAT-002 — Persistência da matriz técnica no projeto
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.3  
**Implementação:** a matriz 100×100 é armazenada no estado do projeto como PNG codificado em base64, além de poder ser exportada manualmente.  
**Objetivo:** permitir reabrir o `.pixelart.json` e continuar a partir da matriz aprovada sem depender do arquivo exportado.

### MAT-003 — Comparação visual antes da aprovação
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.3  
**Implementação:** Pixel Art aprovada e matriz 100×100 são exibidas lado a lado. A grade pode ser ligada apenas para inspeção.  
**Objetivo:** garantir que a mudança de arquitetura seja aprovada antes da redução de cores.


### CHECKPOINT — Aprovação da v0.3
**Status:** CONCLUÍDO  
**Data:** 13/10/2026  
**Resultado:** a etapa Matriz lógica 100×100 foi aprovada para continuidade do fluxo.

### SIM-004 — Composição automática da paleta final
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.4  
**Implementação:** cores essenciais entram primeiro; vagas restantes são preenchidas com RGBs reais da matriz usando diversidade em Lab com peso de frequência.  
**Objetivo:** completar 50 cores sem voltar ao comportamento problemático do Median Cut simples.

### SIM-005 — Uso obrigatório das cores essenciais
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.4  
**Implementação:** se uma essencial não aparecer naturalmente no remapeamento, o sistema a reinsere em uma célula pertencente preferencialmente à área onde foi selecionada.  
**Objetivo:** garantir que “protegida” signifique presença real no resultado e futura legenda.


### CHECKPOINT — Aprovação da v0.4
**Status:** CONCLUÍDO  
**Data:** 13/10/2026  
**Resultado:** a etapa de simplificação para 50 cores foi aprovada para continuidade.

### MAN-002 — Persistência da edição manual
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.5  
**Implementação:** a matriz editada 100×100 é armazenada no estado do projeto e vinculada à versão simplificada de origem.  
**Objetivo:** fechar e reabrir o projeto sem perder ajustes manuais.

### MAN-003 — Paleta final integrada ao editor
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.5  
**Implementação:** o editor aceita somente os 50 RGBs finais; essenciais aparecem agrupadas pelas áreas de origem e as demais em grupo complementar.  
**Objetivo:** impedir criação acidental de uma 51ª cor e preservar o contexto das cores.

### BUG-003 — Assinatura instável da simplificação
**Status:** CONCLUÍDO  
**Versão:** v0.5  
**Problema:** a v0.4 usava `hash()` do Python na assinatura da entrada, e esse valor muda entre sessões.  
**Correção:** substituição por SHA-256 estável e migração automática de resultados v0.4 salvos.


### CHECKPOINT — Aprovação da v0.5
**Status:** CONCLUÍDO  
**Data:** 14/10/2026  
**Resultado:** o Editor Manual integrado foi aprovado.

### UX-009 — Zoom e pan nas etapas visuais de precisão
**Status:** AGUARDANDO AVALIAÇÃO  
**Versão:** v0.5.1  
**Decisão:** zoom deve estar disponível tanto na seleção de áreas quanto na edição manual.  
**Seleção de áreas:** funcionalidade já existente foi mantida como padrão oficial.  
**Edição manual:** adicionado zoom ancorado no cursor, botões +/−, Ajustar e pan por botão do meio ou Shift + arrastar.  
**Regra:** zoom/pan afetam apenas a visualização; máscaras e células lógicas continuam usando as coordenadas reais.
