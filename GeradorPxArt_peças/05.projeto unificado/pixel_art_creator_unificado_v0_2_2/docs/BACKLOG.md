# BACKLOG — Pixel Art Creator Unificado

**Projeto:** Pixel Art Creator  
**Versão-base atual:** v0.2.2  
**Última atualização:** 06/10/2026  
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
| MAT-001 | Integrar enquadramento/matriz lógica 100×100 | PLANEJADO | Após v0.2 |
| SIM-001 | Integrar simplificação padrão para 50 cores | PLANEJADO | Após matriz |
| SIM-002 | Garantir proteção das cores essenciais | PLANEJADO | Simplificação |
| SIM-003 | Melhorar tratamento de grandes blocos sólidos de uma cor | IDEIA / BACKLOG | Refinamento |
| MAN-001 | Integrar editor manual aprovado v0.1.4 | PLANEJADO | Etapa de edição |
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
**Status:** PLANEJADO  
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
**Status:** PLANEJADO  
**Decisão oficial:** 50 cores é o padrão; 35 cores perdeu qualidade nos testes.  
**Plano:**
- iniciar pelas cores essenciais;
- completar até 50 com cores relevantes da imagem;
- preservar famílias cromáticas e contraste;
- não alterar a geometria da Pixel Art;
- sem dithering aleatório.

### SIM-002 — Proteção de cores essenciais
**Status:** PLANEJADO  
**Plano:** toda cor marcada como essencial precisa sobreviver à simplificação, salvo decisão manual explícita da usuária.

### SIM-003 — Tratamento de blocos sólidos
**Status:** IDEIA / BACKLOG  
**Problema:** grandes regiões 4-conectadas de uma mesma cor podem achatar volume e textura.  
**Plano futuro:** detectar componentes grandes e sugerir recuperação de nuances da própria paleta guiada pela imagem anterior à simplificação. A edição manual permanece como garantia final.

---

### MAN-001 — Integração do editor manual
**Status:** PLANEJADO  
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

**Última atividade concluída:** avaliação e aprovação da estrutura v0.1; desenvolvimento da v0.2 com Áreas + Paletas + Cores Essenciais.  
**Próxima ação:** avaliação da v0.2 pela usuária.  
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
