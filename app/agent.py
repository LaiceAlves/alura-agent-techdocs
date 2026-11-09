"""Agente de perguntas e respostas sobre documentação técnica."""

import os
from functools import lru_cache
from pathlib import Path

from google import genai

from .document_loader import carregar_texto_pdf, dividir_em_trechos


# Localização do documento PDF no projeto
BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = (
    BASE_DIR
    / "data"
    / "documentacao_tecnica_techdocs_oracle.pdf"
)

MODEL_NAME = "gemini-3.8-flash"


@lru_cache(maxsize=1)
def carregar_documentacao():
    """Carrega o PDF e divide seu conteúdo em trechos."""

    texto = carregar_texto_pdf(PDF_PATH)

    return dividir_em_trechos(
        texto,
        tamanho_trecho=800,
        sobreposicao=150
    )


def buscar_trechos(pergunta, quantidade=3):
    """Busca os trechos mais relevantes para a pergunta."""

    palavras_ignoradas = {
        "a", "o", "as", "os", "de", "da", "do",
        "das", "dos", "em", "no", "na", "nos",
        "nas", "um", "uma", "e", "ou", "qual",
        "quais", "como", "que", "é", "para",
        "por", "com", "sobre", "me", "sua",
        "seu", "empresa"
    }

    palavras = [
        palavra
        for palavra in pergunta.lower().split()
        if palavra not in palavras_ignoradas
    ]

    resultados = []

    if not palavras:
        return []

    trechos = carregar_documentacao()

    for i, trecho in enumerate(trechos):

        texto = trecho.lower()

        pontuacao = sum(
            1 for palavra in palavras
            if palavra in texto
        )

        relevancia = pontuacao / len(palavras)

        if pontuacao >= 1 and relevancia >= 0.5:

            # Dá prioridade ao título da seção
            if "4. fluxo de suporte técnico" in texto:
                pontuacao += 5

                # Acrescenta o próximo trecho quando necessário
                if (
                    i + 1 < len(trechos)
                    and "passo 1" in texto
                ):
                    trecho = trecho + "\n" + trechos[i + 1]

            resultados.append((pontuacao, trecho))

    resultados.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return resultados[:quantidade]


def perguntar_ao_agente(pergunta):
    """Envia a pergunta e o contexto relevante para o Gemini."""

    resultados = buscar_trechos(pergunta)

    if not resultados:
        return "Não encontrei informações relevantes no documento."

    contexto = "\n\n".join(
        trecho for pontuacao, trecho in resultados
    )

    # Recupera a chave da API sem deixá-la exposta no código
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "A variável de ambiente GEMINI_API_KEY não foi configurada."
        )

    client = genai.Client(api_key=api_key)

    prompt = f"""
Você é o TechDocs Agent, um assistente de documentação técnica.

Responda à pergunta usando apenas as informações presentes
no contexto abaixo.

Se o contexto não contiver a resposta, informe que não encontrou
informação suficiente no documento.

CONTEXTO:
{contexto}

PERGUNTA:
{pergunta}
"""

    resposta = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return resposta.text or "Não foi possível gerar uma resposta."
