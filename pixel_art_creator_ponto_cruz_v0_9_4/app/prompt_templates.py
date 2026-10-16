from textwrap import dedent


def _size_guidance(width: int, height: int) -> str:
    max_side = max(width, height)
    min_side = min(width, height)
    total = width * height

    header = (
        f"MATRIZ-ALVO\n"
        f"- Pense a imagem já orientada para uma grade final de {width}×{height} pontos ({total} células).\n"
        f"- Não desenhe grade, números, letras, símbolos, legenda ou marcações por cima da imagem.\n"
        f"- Distribua formas, volumes e manchas de cor de modo que continuem legíveis quando a imagem for convertida para essa grade."
    )

    if max_side <= 50:
        specific = dedent(
            """
            - Como a escala é pequena, simplifique bastante formas secundárias e microdetalhes.
            - Preserve com prioridade máxima olhos, nariz, boca/língua, expressão, silhueta e acessórios importantes.
            - Em olhos e focinho, organize bem os pixels escuros e claros para que a leitura continue forte mesmo em poucos pontos.
            - Evite serrilhados desnecessários, manchas isoladas e detalhes tão pequenos que virem ruído no bordado.
            """
        ).strip()
    elif max_side >= 100 or min_side >= 100:
        specific = dedent(
            """
            - Como a escala é maior, você pode manter mais detalhe estrutural, mas ainda com leitura limpa e organizada.
            - Preserve melhor a expressão, o brilho natural dos olhos e a distribuição dos tons do rosto.
            - Mesmo com mais detalhe, continue evitando excesso de nuances quase idênticas e ruído fotográfico.
            """
        ).strip()
    else:
        specific = dedent(
            """
            - Use um nível intermediário de simplificação: preserve detalhes importantes, mas elimine ruídos e microtexturas inúteis para o bordado.
            - Garanta boa leitura dos olhos, focinho, expressão, volumes principais e acessórios marcantes.
            """
        ).strip()

    return header + "\n" + specific


def _outline_guidance(outline: bool) -> str:
    if outline:
        return dedent(
            """
            CONTORNO
            - Adicione contorno seletivo apenas onde ele realmente ajudar a leitura do bordado.
            - Prefira contornos em tons escuros harmonizados com a própria paleta, em vez de preto puro em toda a imagem.
            - Não contorne cada detalhe interno.
            - Não use linhas excessivamente grossas.
            """
        ).strip()

    return dedent(
        """
        CONTORNO
        - Não adicione contorno preto externo nem line art artificial.
        - Diferencie as formas por contraste entre sombra, meio-tom e luz.
        - Preserve apenas linhas naturalmente escuras que realmente façam parte da leitura da imagem.
        """
    ).strip()


def build_cross_stitch_prompt(width: int = 50, height: int = 50, color_limit: int = 50, outline: bool = False) -> str:
    prompt = dedent(
        f"""
        Use a imagem anexada como referência e transforme-a em uma ILUSTRAÇÃO EM PIXEL ART/CARTOON pensada como BASE PARA UM GRÁFICO DE BORDADO EM PONTO CRUZ.

        O objetivo não é reproduzir a fotografia pixel por pixel. O objetivo é criar uma versão desenhada, simplificada, colorida e claramente reconhecível, que sirva como base para um futuro gráfico de bordado.

        PRIORIDADES GERAIS
        - Preserve composição, enquadramento, pose, proporções, silhueta, expressão e elementos característicos.
        - Preserve cores realmente importantes para reconhecer o sujeito, mas trate as demais cores com liberdade artística.
        - Use uma paleta mais viva, alegre e ilustrada do que a fotografia, sem transformar a imagem em neon artificial.
        - Simplifique detalhes fotográficos pequenos.
        - Agrupe pelos, cabelos, vegetação e outras texturas em mechas, massas e formas gráficas maiores.
        - Organize sombra, meio-tom e luz em faixas claramente diferenciadas.
        - Evite muitas nuances quase iguais lado a lado.
        - Evite ruído de pequenos detalhes isolados que não seriam úteis em um bordado.

        PALETA E CORES
        - Trabalhe pensando em aproximadamente até {color_limit} cores principais ou famílias cromáticas úteis para o bordado.
        - Não precisa contar matematicamente as cores, mas a imagem deve ficar compatível com uma futura limitação próxima desse valor.
        - Se duas cores muito próximas puderem ser representadas por uma só sem perda importante, prefira simplificar.
        - Preserve especialmente os contrastes importantes do rosto, olhos, nariz, boca/língua e acessórios.

        PIXELS E ACABAMENTO
        - Cada bloco/pixel visível deve ter uma única cor sólida.
        - Não use blur, anti-aliasing, gradientes suaves nem mistura de cores dentro do mesmo bloco.
        - Não invente brilhos, reflexos ou pontos de luz decorativos.
        - Preserve apenas os pontos de luz realmente necessários para a leitura do volume e da expressão.
        - Não adicione textos, grade, números, símbolos ou legenda.

        EXPRESSÃO E LEITURA
        - Dê atenção especial à expressão do rosto e à leitura dos olhos.
        - Os olhos devem continuar claramente visíveis, com boa distribuição dos tons escuros e claros, evitando a sensação de olhos apagados ou deformados.
        - O nariz, a boca e demais pontos de foco devem permanecer reconhecíveis e bem organizados.

        {_size_guidance(width, height)}

        {_outline_guidance(outline)}

        IMPORTANTE
        - Gere uma imagem final limpa, artística e intencional, pronta para servir de base a um gráfico de ponto cruz.
        - Não desenhe a grade do bordado por cima da imagem.
        - O sistema fará depois a parte técnica de grade exata, paleta detalhada, legenda e exportação.
        """
    ).strip()
    return prompt


PROMPT_50_SEM_CONTORNO = build_cross_stitch_prompt(50, 50, 50, False)
PROMPT_50_COM_CONTORNO = build_cross_stitch_prompt(50, 50, 50, True)
PROMPT_100_SEM_CONTORNO = build_cross_stitch_prompt(100, 100, 50, False)
PROMPT_100_COM_CONTORNO = build_cross_stitch_prompt(100, 100, 50, True)


# Backward-compatible aliases expected by earlier code.
PROMPT_SEM_CONTORNO = PROMPT_50_SEM_CONTORNO
PROMPT_COM_CONTORNO = PROMPT_50_COM_CONTORNO


def get_prompt(kind: str, width: int = 50, height: int = 50, color_limit: int = 50) -> str:
    return build_cross_stitch_prompt(
        width=width,
        height=height,
        color_limit=color_limit,
        outline=(kind == "com_contorno"),
    )


def build_matrix_refinement_prompt(width: int = 50, height: int = 50, color_limit: int = 50, outline: bool = False) -> str:
    """Prompt used in the second artistic ChatGPT pass.

    This pass is intentionally different from the initial illustration prompt:
    it asks ChatGPT to redraw the already-approved pixel/cartoon base specifically
    for the target stitch matrix, preserving focal details artistically before the
    local app performs only a technical normalization.
    """
    contour = _outline_guidance(outline)
    small_grid = max(width, height) <= 60
    preservation = dedent(
        """
        PROTEÇÃO DE DETALHES IMPORTANTES
        - Preserve a expressão como prioridade máxima.
        - Preserve o formato dos dois olhos, sua posição e a distribuição interna entre preto/marrom/reflexo.
        - Mantenha pelo menos um brilho claro em cada olho somente quando ele existir na imagem-base e for necessário para que o olho continue vivo e legível.
        - Não deixe áreas escuras dos olhos se fundirem com o pelo ao redor.
        - Preserve nariz, focinho, boca, língua e acessórios importantes.
        - Se precisar eliminar detalhes, elimine primeiro ruído de fundo, grama e microtexturas secundárias.
        """
    ).strip()
    if small_grid:
        preservation += "\n- Como a matriz é pequena, exagere levemente a legibilidade dos olhos e do focinho em vez de sacrificá-los à simplificação."

    return dedent(
        f"""
        Use a IMAGEM PIXEL ART/CARTOON ANEXADA como base já aprovada e RECRIE-A ARTISTICAMENTE para funcionar como uma MATRIZ DE BORDADO EM PONTO CRUZ de {width}×{height} pontos.

        Esta é uma etapa de REDESENHO ARTÍSTICO ORIENTADO À MATRIZ. Não faça apenas um redimensionamento mecânico da imagem.

        OBJETIVO
        - Reorganize visualmente formas e blocos de cor para que o desenho continue reconhecível e expressivo em aproximadamente {width} colunas × {height} linhas.
        - Pense que cada bloco lógico importante precisará virar um ponto de bordado.
        - Mantenha a composição, pose, silhueta e identidade visual da imagem-base.
        - Não desenhe grade, números, letras, símbolos ou legenda sobre a imagem.

        {preservation}

        PALETA
        - Trabalhe já com uma paleta visualmente simplificada, compatível com até {color_limit} cores úteis.
        - Evite tons quase duplicados.
        - Una cores muito próximas quando isso não prejudicar a leitura.
        - Preserve contrastes importantes nos olhos, rosto, nariz, língua e acessórios.
        - Não transforme áreas importantes em manchas chapadas quando sombra/meio-tom/luz forem necessários para leitura.

        PIXELS / BLOCOS
        - Cada bloco visível deve ter apenas UMA cor sólida.
        - Não use blur, anti-aliasing, gradiente suave ou mistura de cores dentro do mesmo bloco.
        - Use formas em degraus e agrupamentos claros de pixels.
        - Evite ruído de pontos isolados sem função visual.

        MATRIZ-ALVO
        - O desenho final deve ser concebido especificamente para {width}×{height} pontos.
        - Não precisa exportar um arquivo fisicamente de {width}×{height} pixels; o importante é que a COMPOSIÇÃO VISUAL seja pensada para essa quantidade de pontos.
        - O aplicativo fará depois apenas a normalização técnica para a grade exata, sem redesenhar artisticamente.

        {contour}

        RESULTADO ESPERADO
        - Uma pixel art/cartoon bordável, limpa e intencional.
        - Expressão, olhos e focinho claramente legíveis.
        - Paleta visual já simplificada.
        - Distribuição de cores adequada ao futuro gráfico de ponto cruz.
        - Sem textos, sem grade e sem legenda.
        """
    ).strip()
