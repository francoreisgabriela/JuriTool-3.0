# ⚖️ JuriToolbox — Caixa de Ferramentas Jurídicas (Versão Educacional)

O **JuriToolbox** é um aplicativo interativo desenvolvido em **Python + Streamlit**, projetado para apoiar estudantes no estudo de Direito Penal e Processual Penal. Ele utiliza arquivos CSV contendo versões estruturadas do **Código Penal (CP)** e do **Código de Processo Penal (CPP)** para permitir buscas, análises e simulações.

> ⚠️ **Aviso importante**  
> Este projeto tem finalidade **exclusivamente educacional**.  
> O aplicativo **não substitui** consulta jurídica, parecer profissional ou análise de caso concreto.  
> As regras adotadas são **simplificadas**.

---

# 📁 Funcionalidades

## 🔹 1. Seleção e Consulta de Crimes (via CP e CPP em CSV)

O usuário seleciona um crime diretamente a partir do `cp.csv`.  
Em seguida, o programa:

- Localiza automaticamente todas as informações correspondentes ao crime no **Código Penal**;
- Procura referências relacionadas no **CPP** utilizando heurísticas simples;
- Exibe tabelas, textos e ementas formatadas conforme encontradas nos CSVs.

Esta função é ideal para estudo rápido e navegação entre dispositivos legais.

---

## 🔹 2. Elegibilidade ao ANPP (art. 28-A do CPP)

Checklist totalmente revisado e funcional baseado no art. 28-A do CPP.

O módulo:

- Exibe o texto do artigo 28-A (a partir do `cpp.csv`);
- Pergunta sobre cada requisito legal (violência, pena mínima, confissão, reincidência etc.);
- Gera automaticamente um **parecer explicativo** em linguagem natural, indicando se o caso seria ou não elegível ao ANPP segundo os critérios educacionais.

Critérios incluídos:

- Ausência de violência ou grave ameaça  
- Pena mínima inferior a 4 anos  
- Confissão formal  
- Não reincidência dolosa  
- Não violência doméstica/gênero  
- Não concessão prévia de ANPP  

---

## 🔹 3. Dosimetria Simplificada (art. 59 do CP)

Simulador didático da dosimetria penal:

### 1ª etapa — Pena-base  
Avaliação das 8 circunstâncias judiciais:

- Culpabilidade  
- Antecedentes  
- Conduta social  
- Personalidade  
- Motivos  
- Circunstâncias  
- Consequências  
- Comportamento da vítima  

O usuário escolhe: **Favorável**, **Neutra**, **Desfavorável**.  
Cada escolha altera a pena-base numericamente de maneira didática.

### 2ª e 3ª etapas — Causas de aumento/diminuição  
O usuário pode adicionar causas com:

- Tipo: Aumento ou Diminuição  
- Valor percentual (ex.: 0.333 para 1/3)  
- Descrição textual

### Resultado  
O programa:

- Calcula pena-base → pena intermediária → pena definitiva  
- Converte o resultado em anos e meses  
- Gera um **rascunho de fundamentação jurídica**, ideal para estudos e trabalhos acadêmicos

---

# 🗂️ Estrutura do Projeto
