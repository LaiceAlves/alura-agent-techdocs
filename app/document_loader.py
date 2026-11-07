"""Leitura e divisão de documentos PDF do TechDocs Agent."""

from pathlib import Path

from pypdf import PdfReader


def carregar_texto_pdf(caminho_pdf: str | Path) -> str:
    """Extrai e retorna o texto de todas as páginas de um PDF."""
    caminho = Path(caminho_pdf)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo PDF não encontrado: {caminho}. "
            "Confira se o documento está na pasta data/."
        )

    leitor = PdfReader(str(caminho))
    paginas = []

    for numero_pagina, pagina in enumerate(leitor.pages, start=1):
        texto_pagina = pagina.extract_text() or ""
        if texto_pagina.strip():
            paginas.append(texto_pagina)

    texto_documento = "\n\n".join(paginas).strip()

    if not texto_documento:
        raise ValueError(
            "Não foi possível extrair texto do PDF. "
            "Verifique se o arquivo contém texto selecionável."
        )

    return texto_documento


def dividir_em_trechos(
    texto: str,
    tamanho_trecho: int = 800,
    sobreposicao: int = 150,
) -> list[str]:
    """Divide o texto em trechos com sobreposição entre blocos consecutivos."""
    if tamanho_trecho <= 0:
        raise ValueError("tamanho_trecho deve ser maior que zero.")

    if sobreposicao < 0 or sobreposicao >= tamanho_trecho:
        raise ValueError(
            "sobreposicao deve ser maior ou igual a zero e menor que tamanho_trecho."
        )

    texto = texto.strip()
    if not texto:
        return []

    trechos = []
    passo = tamanho_trecho - sobreposicao

    for inicio in range(0, len(texto), passo):
        trecho = texto[inicio : inicio + tamanho_trecho].strip()
        if trecho:
            trechos.append(trecho)

    return trechos
