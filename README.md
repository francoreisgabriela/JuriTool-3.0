# ⚖️ JuriToolbox — Caixa de Ferramentas Jurídicas (Versão Educacional)

O **JuriToolbox** é um aplicativo interativo desenvolvido em **Python + Streamlit**, voltado para estudantes de Direito que queiram visualizar e experimentar, de forma didática, conceitos de Direito Penal e Processual Penal usando dados estruturados em CSV.

> ⚠️ **Aviso importante**  
> Este projeto tem **finalidade exclusivamente educacional**.  
> O aplicativo **não substitui** consulta jurídica, parecer profissional ou análise de caso concreto.  
> As regras implementadas são propositalmente **simplificadas**.

---

## 📁 Funcionalidades

### 🔹 1. Consulta de Artigos no CP e CPP (via CSV)

O usuário informa um **artigo** (ex.: `155`, `171`, `121`, `28-A`) em um campo de texto.

O aplicativo então:

- Busca esse artigo na base `CP_Codigo_Penal.s.csv` (Código Penal);
- Busca o mesmo artigo na base `CPP_Codigo_Processo_Penal.s.csv` (Código de Processo Penal);
- Exibe o(s) texto(s) correspondente(s), usando as colunas de artigo e texto/descrição identificadas automaticamente.

O código tenta ser tolerante com o formato das colunas, procurando por nomes como:

- `art`, `artigo`, `artigo_numero` (para o número do artigo)
- `texto`, `descricao`, `ementa`, `conteudo` (para o conteúdo do artigo)

---

### 🔹 2. Elegibilidade ao ANPP (art. 28-A do CPP)

Módulo de checklist **didático** baseado no art. 28-A do CPP.

Funcionalidades:

- Tenta localizar e exibir o **texto do art. 28-A** na base `CPP_Codigo_Processo_Penal.s.csv`;
- Apresenta um conjunto de perguntas ao usuário, incluindo:
  - Fato sem violência ou grave ameaça à pessoa?
  - Pena mínima em abstrato inferior a 4 anos?
  - Há confissão formal e circunstanciada?
  - Há reincidência em crime doloso?
  - Situação envolve violência doméstica/familiar ou contra a mulher por razões de gênero?
  - Já houve concessão prévia de ANPP em caso semelhante?

Com base nessas respostas, o módulo:

- Indica se, **em tese**, o caso seria **potencialmente elegível** ao ANPP, segundo critérios simplificados;
- Gera um **parecer em linguagem natural**, com explicações e ressalvas quanto ao caráter educacional do modelo.

---

### 🔹 3. Dosimetria Simplificada (art. 59 do CP)

Simulador numérico da dosimetria da pena com base em parâmetros simplificados.

#### Etapas:

1. **Definição dos limites abstratos**  
   O usuário informa a pena mínima e máxima em anos (ex.: 1 a 4 anos).

2. **Avaliação das circunstâncias judiciais (art. 59 CP)**  
   Para cada uma das 8 circunstâncias, o usuário escolhe:
   - **Desfavorável**
   - **Neutra**
   - **Favorável**

   Circunstâncias avaliadas:
   - Culpabilidade  
   - Antecedentes  
   - Conduta social  
   - Personalidade  
   - Motivos  
   - Circunstâncias  
   - Consequências  
   - Comportamento da vítima  

   Cada circunstância “puxa” a pena-base para mais ou para menos, de forma numérica e didática.

3. **Causas de aumento e diminuição (simplificadas)**  
   O usuário pode cadastrar causas, cada uma com:
   - Tipo: **Aumento** ou **Diminuição**  
   - Fator: ex.: `0.333` para 1/3  
   - Descrição: ex.: tentativa, concurso de pessoas etc.

   O app aplica essas causas em sequência sobre a pena-base.

4. **Resultado e Fundamentação**  
   O módulo:
   - Calcula a **pena-base** e a **pena final** em anos;
   - Faz uma conversão aproximada em **anos e meses**;
   - Gera um **rascunho de fundamentação textual**, mencionando as circunstâncias judiciais e as causas de aumento/diminuição, com aviso de que se trata apenas de simulação didática.

---

## 🗂️ Estrutura do Projeto

```text
JuriToolbox/
│
├── app.py                              # Aplicativo principal (Streamlit)
├── CP_Codigo_Penal.s.csv               # Código Penal estruturado em CSV
├── CPP_Codigo_Processo_Penal.s.csv     # Código de Processo Penal estruturado em CSV
└── README.md                           # Este arquivo
