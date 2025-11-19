import streamlit as st
import pandas as pd

# ==========================
# CARREGAMENTO DAS BASES (CP e CPP)
# ==========================

@st.cache_data
def carregar_codigo(caminho):
    try:
        df = pd.read_csv(caminho)
        return df
    except FileNotFoundError:
        st.warning(f"Arquivo não encontrado: {caminho}. "
                   f"Verifique se o arquivo está na mesma pasta do app.py.")
        return None
    except Exception as e:
        st.warning(f"Erro ao ler {caminho}: {e}")
        return None


def detectar_coluna_artigo(df):
    if df is None:
        return None
    candidatos = [c for c in df.columns if "art" in c.lower()]
    return candidatos[0] if candidatos else None


def detectar_coluna_texto(df):
    if df is None:
        return None
    candidatos = [
        c for c in df.columns
        if "texto" in c.lower()
        or "descr" in c.lower()
        or "ementa" in c.lower()
        or "conteudo" in c.lower()
    ]
    return candidatos[0] if candidatos else None


def buscar_artigo(df, artigo_str):
    """
    Busca um artigo em um DataFrame (CP ou CPP) de forma tolerante.
    - Primeiro tenta pela coluna de artigo (igualdade ou 'contains')
    - Depois tenta 'contains' na coluna de texto.
    Retorna uma string com o(s) resultado(s) ou None.
    """
    if df is None or not artigo_str:
        return None

    artigo_str = str(artigo_str).strip().lower()
    col_art = detectar_coluna_artigo(df)
    col_txt = detectar_coluna_texto(df)

    # 1) Busca pela coluna de artigo (mais estruturado)
    if col_art:
        serie_art = df[col_art].astype(str).str.strip().str.lower()
        # primeiro: igualdade
        mask = (serie_art == artigo_str)
        resultado = df[mask]
        # se nada, tenta contains (útil pra "28-A" quando a coluna tem "Art. 28-A")
        if resultado.empty:
            mask = serie_art.str.contains(artigo_str, na=False)
            resultado = df[mask]

        if not resultado.empty:
            if col_txt:
                return "\n\n---\n\n".join(resultado[col_txt].astype(str).tolist())
            else:
                return resultado.to_string(index=False)

    # 2) Busca no texto (fallback)
    if col_txt:
        serie_txt = df[col_txt].astype(str).str.lower()
        mask = serie_txt.str.contains(artigo_str, na=False)
        resultado = df[mask]
        if not resultado.empty:
            return "\n\n---\n\n".join(resultado[col_txt].astype(str).tolist())

    return None


# ==========================
# ANPP – Elegibilidade (art. 28-A CPP)
# ==========================

def analisar_anpp(sem_violencia, pena_min_inferior_4, confissao,
                  reincidente_doloso, crime_domestico, ja_teve_anpp):
    motivos_nao = []

    if not sem_violencia:
        motivos_nao.append("O fato envolve violência ou grave ameaça à pessoa.")
    if not pena_min_inferior_4:
        motivos_nao.append("A pena mínima em abstrato não é inferior a 4 anos.")
    if not confissao:
        motivos_nao.append("Não há confissão formal e circunstanciada do investigado.")
    if reincidente_doloso:
        motivos_nao.append("O investigado é reincidente em crime doloso.")
    if crime_domestico:
        motivos_nao.append(
            "O fato guarda relação com violência doméstica/familiar ou contra a mulher por razões do sexo feminino."
        )
    if ja_teve_anpp:
        motivos_nao.append(
            "O investigado já foi beneficiado por ANPP anterior em situação semelhante (regra simplificada do app)."
        )

    elegivel = (len(motivos_nao) == 0)

    if elegivel:
        parecer = (
            "À luz dos parâmetros **simplificados** adotados neste aplicativo, o caso é, em tese, "
            "**potencialmente elegível** ao Acordo de Não Persecução Penal (art. 28-A do CPP). "
            "Os requisitos considerados foram atendidos:\n\n"
            "- Fato sem violência ou grave ameaça;\n"
            "- Pena mínima inferior a 4 (quatro) anos;\n"
            "- Confissão formal e circunstanciada do investigado;\n"
            "- Ausência de reincidência dolosa relevante ou contexto impeditivo.\n\n"
            "⚠️ **Atenção:** Esta análise é apenas **didática**. A aplicação concreta do ANPP depende da "
            "interpretação do Ministério Público, da análise do caso concreto e da jurisprudência atual."
        )
    else:
        parecer = "Neste modelo simplificado, o caso foi considerado **não elegível** ao ANPP pelos seguintes motivos:\n\n"
        for m in motivos_nao:
            parecer += f"- {m}\n"
        parecer += (
            "\n⚠️ **Importante:** Trata-se de um checklist educacional. A avaliação real deve ser feita "
            "pelo Ministério Público e pelos profissionais do Direito, com base no caso concreto."
        )

    return elegivel, parecer


# ==========================
# Dosimetria (art. 59 do CP)
# ==========================

def calcular_pena_base(pena_min, pena_max, avaliacao_fatores):
    intervalo = pena_max - pena_min
    desfavoraveis = sum(1 for v in avaliacao_fatores.values() if v == "Desfavorável")
    favoraveis = sum(1 for v in avaliacao_fatores.values() if v == "Favorável")

    ajuste = (desfavoraveis - favoraveis) * (intervalo / 8.0)
    pena_base = pena_min + ajuste
    pena_base = max(pena_min, min(pena_base, pena_max))
    return pena_base


def aplicar_causas(pena_base, causas):
    pena = pena_base
    for c in causas:
        fator = c.get("fator", 0)
        if fator <= 0:
            continue
        if c.get("tipo") == "Aumento":
            pena *= (1 + fator)
        else:
            pena *= (1 - fator)
    return pena


def formatar_anos(pena_anos):
    anos = int(pena_anos)
    resto = pena_anos - anos
    meses = int(round(resto * 12))
    return anos, meses


def gerar_fundamentacao(pena_min, pena_max, avaliacao_fatores, pena_base, causas, pena_final):
    texto = []

    texto.append("**1ª Fase – Pena-base (art. 59 do CP)**\n")

    texto.append(
        f"Considerando os limites abstratos da pena, fixados entre **{pena_min:.2f}** e "
        f"**{pena_max:.2f}** anos, passa-se à análise das circunstâncias judiciais."
    )

    mapeamento_frases = {
        "culpabilidade": "a culpabilidade do agente",
        "antecedentes": "os antecedentes criminais",
        "conduta_social": "a conduta social",
        "personalidade": "a personalidade do agente",
        "motivos": "os motivos do crime",
        "circunstancias": "as circunstâncias do crime",
        "consequencias": "as consequências do crime",
        "comportamento_vitima": "o comportamento da vítima",
    }

    lista_descricoes = []
    for chave, valor in avaliacao_fatores.items():
        if valor == "Neutra":
            continue
        if valor == "Desfavorável":
            lista_descricoes.append(f"- {mapeamento_frases[chave]} mostra-se **desfavorável** ao réu;")
        else:
            lista_descricoes.append(f"- {mapeamento_frases[chave]} revela-se **favorável** ao réu;")

    if lista_descricoes:
        texto.append("\nNa forma do art. 59 do Código Penal, avaliam-se:\n")
        texto.extend(lista_descricoes)
    else:
        texto.append(
            "\nTodas as circunstâncias judiciais foram avaliadas como **neutras**, razão pela qual "
            "a pena-base é fixada próxima ao **mínimo legal**."
        )

    texto.append(
        f"\nDiante desse conjunto, a pena-base é fixada em **{pena_base:.2f} anos**."
    )

    if causas:
        texto.append("\n\n**2ª/3ª Fases – Causas de aumento e diminuição (modelo simplificado)**\n")
        for c in causas:
            sinal = "aumento" if c["tipo"] == "Aumento" else "diminuição"
            texto.append(
                f"- Aplica-se uma causa de **{sinal}** de aproximadamente **{c['fator']*100:.1f}%** "
                f"({c.get('descricao', 'sem descrição detalhada')})."
            )
        texto.append(
            f"\nApós a incidência dessas causas, a pena definitiva resulta em **{pena_final:.2f} anos**."
        )
    else:
        texto.append(
            "\n\nNão foram consideradas, neste modelo didático, causas especiais de aumento ou diminuição, "
            "de modo que a pena provisória coincide com a pena-base."
        )

    texto.append(
        "\n\n⚠️ **Aviso importante:** Esta dosimetria é **meramente ilustrativa**, baseada em regras "
        "numéricas simplificadas para fins de estudo. Na prática, a fixação da pena "
        "depende da prova, da fundamentação qualitativa e da jurisprudência aplicável."
    )

    return "\n".join(texto)


# ==========================
# INTERFACE STREAMLIT
# ==========================

st.set_page_config(page_title="JuriToolbox (Educacional)", layout="wide")

st.title("⚖️ JuriToolbox – Versão Educacional")
st.markdown(
    """
    **Aviso:** Este aplicativo é apenas para fins **didáticos**.  
    Não substitui consulta a advogado, Defensoria, Ministério Público ou Judiciário.  
    As regras são propositalmente **simplificadas**.
    """
)

# Carrega CP e CPP
cp_df = carregar_codigo("cp.csv")
cpp_df = carregar_codigo("cpp.csv")

# ==========================
# 1. BUSCA DE ARTIGO NO CP E CPP
# ==========================

st.header("1. Consulta de artigo no CP e CPP (via CSV)")

artigo_input = st.text_input(
    "Informe o artigo do crime (ex.: 155, 171, 121, 28-A):",
    help="O programa vai buscar esse artigo nas bases cp.csv e cpp.csv."
)

if st.button("Buscar artigos no CP e CPP"):
    if not artigo_input:
        st.warning("Digite um artigo para buscar (ex.: 155, 28-A).")
    else:
        st.subheader("📚 Resultado no Código Penal (CP)")
        texto_cp = buscar_artigo(cp_df, artigo_input)
        if texto_cp:
            st.code(texto_cp)
        else:
            st.info("Não encontrei esse artigo no cp.csv (verifique o CSV e o formato da coluna).")

        st.subheader("📚 Resultado no Código de Processo Penal (CPP)")
        texto_cpp = buscar_artigo(cpp_df, artigo_input)
        if texto_cpp:
            st.code(texto_cpp)
        else:
            st.info("Não encontrei esse artigo no cpp.csv (verifique o CSV e o formato da coluna).")

st.markdown("---")

# ==========================
# MENU LATERAL – MÓDULOS
# ==========================

modulo = st.sidebar.radio(
    "Escolha o módulo:",
    [
        "2. Elegibilidade ao ANPP (art. 28-A do CPP)",
        "3. Dosimetria Simplificada (art. 59 do CP)"
    ]
)

# ==========================
# 2. ANPP
# ==========================

if modulo.startswith("2."):
    st.header("2. Elegibilidade ao ANPP (art. 28-A do CPP)")

    st.markdown(
        """
        Checklist **simplificado** para estudo dos requisitos do art. 28-A do CPP.  
        Não é uma decisão real, apenas uma ferramenta didática.
        """
    )

    st.subheader("🧾 Texto do art. 28-A do CPP (a partir do CSV, se disponível)")
    texto_28a = buscar_artigo(cpp_df, "28-A")
    if texto_28a:
        st.code(texto_28a)
    else:
        st.info("Não encontrei o art. 28-A no cpp.csv. Verifique o arquivo e o formato dos artigos.")

    st.subheader("Checklist")

    col1, col2 = st.columns(2)
    with col1:
        sem_violencia = st.checkbox("Fato sem violência ou grave ameaça à pessoa?")
        pena_min_inferior_4 = st.checkbox("Pena mínima em abstrato inferior a 4 anos?")
        confissao = st.checkbox("Há confissão formal e circunstanciada do investigado?")

    with col2:
        reincidente_doloso = st.checkbox("Investigado é reincidente em crime doloso?", value=False)
        crime_domestico = st.checkbox(
            "O fato envolve violência doméstica/familiar ou contra a mulher por razões do sexo feminino?",
            value=False
        )
        ja_teve_anpp = st.checkbox("Investigado já foi beneficiado por ANPP em caso semelhante?", value=False)

    if st.button("Analisar elegibilidade (modelo didático)"):
        elegivel, parecer = analisar_anpp(
            sem_violencia,
            pena_min_inferior_4,
            confissao,
            reincidente_doloso,
            crime_domestico,
            ja_teve_anpp
        )

        if elegivel:
            st.success("Resultado: caso potencialmente elegível ao ANPP (em tese).")
        else:
            st.error("Resultado: caso considerado não elegível ao ANPP neste modelo simplificado.")

        st.markdown("### Parecer gerado:")
        st.markdown(parecer)

# ==========================
# 3. DOSIMETRIA
# ==========================

elif modulo.startswith("3."):
    st.header("3. Dosimetria Simplificada (art. 59 do CP)")

    st.markdown(
        """
        Simulação **didática** da dosimetria da pena com base no art. 59 do CP.
        """
    )

    col_limites1, col_limites2 = st.columns(2)
    with col_limites1:
        pena_min = st.number_input("Pena mínima em abstrato (anos)", min_value=0.0, value=1.0, step=0.5)
    with col_limites2:
        pena_max = st.number_input("Pena máxima em abstrato (anos)", min_value=0.0, value=4.0, step=0.5)

    if pena_max < pena_min:
        st.error("A pena máxima não pode ser menor que a pena mínima.")

    st.subheader("Circunstâncias judiciais (art. 59 CP)")
    opcoes = ["Desfavorável", "Neutra", "Favorável"]

    col1, col2, col3 = st.columns(3)
    with col1:
        culpabilidade = st.selectbox("Culpabilidade", opcoes, index=1)
        antecedentes = st.selectbox("Antecedentes", opcoes, index=1)
        conduta_social = st.selectbox("Conduta social", opcoes, index=1)
    with col2:
        personalidade = st.selectbox("Personalidade", opcoes, index=1)
        motivos = st.selectbox("Motivos", opcoes, index=1)
        circunstancias = st.selectbox("Circunstâncias", opcoes, index=1)
    with col3:
        consequencias = st.selectbox("Consequências", opcoes, index=1)
        comportamento_vitima = st.selectbox("Comportamento da vítima", opcoes, index=1)

    avaliacao_fatores = {
        "culpabilidade": culpabilidade,
        "antecedentes": antecedentes,
        "conduta_social": conduta_social,
        "personalidade": personalidade,
        "motivos": motivos,
        "circunstancias": circunstancias,
        "consequencias": consequencias,
        "comportamento_vitima": comportamento_vitima,
    }

    st.subheader("Causas de aumento/diminuição (ilustrativas)")
    num_causas = st.number_input("Número de causas especiais", min_value=0, max_value=5, value=0, step=1)

    causas = []
    for i in range(num_causas):
        st.markdown(f"**Causa {i+1}:**")
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            tipo = st.selectbox(f"Tipo {i+1}", ["Aumento", "Diminuição"], key=f"tipo_{i}")
        with c2:
            fator = st.number_input(
                f"Fator (ex.: 0.333 para 1/3)", 
                min_value=0.0, max_value=5.0, value=0.3333, step=0.05,
                key=f"fator_{i}"
            )
        with c3:
            desc = st.text_input(
                f"Descrição (ex.: tentativa, concurso de pessoas...)", 
                key=f"desc_{i}"
            )
        causas.append({"tipo": tipo, "fator": fator, "descricao": desc})

    if st.button("Calcular dosimetria (modelo didático)"):
        if pena_max < pena_min:
            st.error("Corrija os limites da pena (máxima ≥ mínima).")
        else:
            pena_base = calcular_pena_base(pena_min, pena_max, avaliacao_fatores)
            pena_final = aplicar_causas(pena_base, causas)

            anos_base, meses_base = formatar_anos(pena_base)
            anos_final, meses_final = formatar_anos(pena_final)

            st.markdown("### Resultado numérico")
            st.write(f"**Pena-base:** {pena_base:.2f} anos ≈ {anos_base} ano(s) e {meses_base} mês(es).")
            st.write(f"**Pena após causas:** {pena_final:.2f} anos ≈ {anos_final} ano(s) e {meses_final} mês(es).")

            fundamentacao = gerar_fundamentacao(
                pena_min, pena_max, avaliacao_fatores, pena_base, causas, pena_final
            )

            st.markdown("---")
            st.markdown("### Rascunho de fundamentação (texto didático)")
            st.markdown(fundamentacao)
