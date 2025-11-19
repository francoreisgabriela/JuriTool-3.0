import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================
# Funções auxiliares de base
# ==========================

@st.cache_data
def carregar_codigo(caminho):
    try:
        df = pd.read_csv(caminho)
        return df
    except FileNotFoundError:
        st.warning(f"Arquivo não encontrado: {caminho}")
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
    candidatos = [c for c in df.columns if "texto" in c.lower() 
                  or "descr" in c.lower() 
                  or "ementa" in c.lower()]
    return candidatos[0] if candidatos else None


def detectar_coluna_crime(df):
    if df is None:
        return None
    candidatos = [c for c in df.columns if "crime" in c.lower() 
                  or "tipo" in c.lower() 
                  or "descricao" in c.lower()]
    return candidatos[0] if candidatos else None


def buscar_artigo_por_numero(df, numero_artigo):
    """
    Tenta localizar o artigo no DF:
    1) pela coluna de artigo (ex: 'artigo')
    2) se não achar, tenta procurar '28-A' ou 'art. 28-A' em alguma coluna de texto.
    """
    if df is None:
        return None

    col_art = detectar_coluna_artigo(df)
    col_txt = detectar_coluna_texto(df)

    # 1) Busca direta pela coluna de artigo
    if col_art:
        # normalizar para texto
        serie = df[col_art].astype(str).str.strip().str.lower()
        alvo = str(numero_artigo).strip().lower()
        resultado = df[serie == alvo]
        if not resultado.empty:
            if col_txt:
                return "\n\n".join(resultado[col_txt].astype(str).tolist())
            else:
                return resultado.to_string(index=False)

    # 2) Busca em texto (fallback)
    if col_txt:
        serie_txt = df[col_txt].astype(str).str.lower()
        alvo = str(numero_artigo).strip().lower()
        resultado = df[serie_txt.str.contains(alvo, na=False)]
        if not resultado.empty:
            return "\n\n".join(resultado[col_txt].astype(str).tolist())

    return None


def listar_crimes_cp(cp_df):
    """
    Tenta criar uma lista de crimes a partir do CP:
    usa coluna com 'crime' ou 'tipo' ou 'descricao'.
    """
    col_crime = detectar_coluna_crime(cp_df)
    if cp_df is None or col_crime is None:
        return []
    valores = cp_df[col_crime].dropna().astype(str).str.strip().unique().tolist()
    valores = sorted(valores)
    return valores


def mostrar_dados_crime(crime_escolhido, cp_df, cpp_df):
    """
    Mostra informações do crime no CP e, se houver, no CPP.
    """
    if not crime_escolhido:
        return

    col_crime_cp = detectar_coluna_crime(cp_df)
    col_txt_cp = detectar_coluna_texto(cp_df)

    st.subheader("📚 Informações do CP relacionadas ao crime selecionado")
    if col_crime_cp is not None:
        filtro = cp_df[col_crime_cp].astype(str).str.strip() == crime_escolhido
        resultado_cp = cp_df[filtro]
        if not resultado_cp.empty:
            if col_txt_cp:
                for _, linha in resultado_cp.iterrows():
                    bloco = ""
                    for c in resultado_cp.columns:
                        bloco += f"**{c}:** {linha[c]}\n"
                    st.markdown("---")
                    st.markdown(bloco)
            else:
                st.dataframe(resultado_cp)
        else:
            st.info("Não encontrei o crime selecionado na base do CP (verifique o CSV).")
    else:
        st.info("Não foi possível identificar uma coluna de 'crime' no CSV do CP.")

    # Agora tenta achar algo no CPP que tenha referência ao mesmo crime (bem heurístico)
    st.subheader("📚 Informações do CPP relacionadas (se houver)")
    if cpp_df is not None:
        col_crime_cpp = detectar_coluna_crime(cpp_df)
        col_txt_cpp = detectar_coluna_texto(cpp_df)

        if col_crime_cpp:
            filtro_cpp = cpp_df[col_crime_cpp].astype(str).str.contains(
                crime_escolhido, case=False, na=False
            )
            resultado_cpp = cpp_df[filtro_cpp]
        elif col_txt_cpp:
            filtro_cpp = cpp_df[col_txt_cpp].astype(str).str.contains(
                crime_escolhido, case=False, na=False
            )
            resultado_cpp = cpp_df[filtro_cpp]
        else:
            resultado_cpp = pd.DataFrame()

        if not resultado_cpp.empty:
            if col_txt_cpp:
                for _, linha in resultado_cpp.iterrows():
                    bloco = ""
                    for c in resultado_cpp.columns:
                        bloco += f"**{c}:** {linha[c]}\n"
                    st.markdown("---")
                    st.markdown(bloco)
            else:
                st.dataframe(resultado_cpp)
        else:
            st.info("Não encontrei referências diretas ao crime no CPP (pelo CSV informado).")
    else:
        st.info("Base do CPP não carregada.")


# ==========================
# ANPP – Elegibilidade
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
            "- Pena mínima inferior a 4 anos;\n"
            "- Confissão formal e circunstanciada;\n"
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
                f"({c.get('descricao', 'sem descrição')})."
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
# Interface Streamlit
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

# Carregar bases
cp_df = carregar_codigo("cp.csv")
cpp_df = carregar_codigo("cpp.csv")

# ==========================
# Seleção de Crime (CP + CPP)
# ==========================

st.header("1. Selecione o crime para consultar CP e CPP")

lista_crimes = listar_crimes_cp(cp_df)

if lista_crimes:
    crime_escolhido = st.selectbox("Crime (a partir da base do CP):", lista_crimes)
    mostrar_dados_crime(crime_escolhido, cp_df, cpp_df)
else:
    st.info("Não consegui montar a lista de crimes. Verifique se o `cp.csv` tem uma coluna como 'crime', 'tipo' ou 'descricao'.")

st.markdown("---")

# ==========================
# Sidebar – Módulos extras
# ==========================

modulo = st.sidebar.radio(
    "Escolha o módulo:",
    [
        "2. Elegibilidade ao ANPP (art. 28-A do CPP)",
        "3. Dosimetria Simplificada (art. 59 do CP)"
    ]
)

# ==========================
# Módulo 2 – ANPP
# ==========================

if modulo.startswith("2."):
    st.header("2. Elegibilidade ao ANPP (art. 28-A do CPP)")

    st.markdown(
        """
        Abaixo, um checklist simplificado para estudar os requisitos do art. 28-A do CPP.  
        O objetivo é **estudo**, não decisão real.
        """
    )

    # Mostrar texto do art. 28-A do CPP, se existir no CSV
    st.subheader("🧾 Texto do art. 28-A do CPP (a partir do CSV, se disponível)")
    texto_28a = buscar_artigo_por_numero(cpp_df, "28-A")
    if texto_28a:
        st.code(texto_28a)
    else:
        st.info("Não encontrei o art. 28-A no `cpp.csv`. Verifique o formato do arquivo.")

    st.subheader("Checklist simplificado")

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
            st.success("Resultado: Caso potencialmente elegível ao ANPP (em tese).")
        else:
            st.error("Resultado: Caso considerado não elegível ao ANPP neste modelo simplificado.")

        st.markdown("### Parecer gerado:")
        st.markdown(parecer)

# ==========================
# Módulo 3 – Dosimetria
# ==========================

elif modulo.startswith("3."):
    st.header("3. Dosimetria Simplificada (art. 59 do CP)")

    st.markdown(
        """
        Simulação didática da dosimetria da pena com base no art. 59 do CP.
        """
    )

    col_art, col_limites = st.columns(2)

    with col_limites:
        pena_min = st.number_input("Pena mínima em abstrato (anos)", min_value=0.0, value=1.0, step=0.5)
        pena_max = st.number_input("Pena máxima em abstrato (anos)", min_value=0.0, value=5.0, step=0.5)

        if pena_max < pena_min:
            st.error("A pena máxima não pode ser menor que a mínima.")

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
        st.markdown(f"**Causa {i + 1}:**")
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
