import re

from transformers import pipeline

MODELO = "Helsinki-NLP/opus-mt-en-fr"
LIMITE_TOKENS = 400


def carregar_tradutor():
    return pipeline("translation_en_to_fr", model=MODELO)


def dividir_em_trechos(texto: str, tokenizer, limite: int = LIMITE_TOKENS) -> list[str]:
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    trechos, atual, tamanho = [], [], 0
    for frase in frases:
        n = len(tokenizer.tokenize(frase))
        if atual and tamanho + n > limite:
            trechos.append(" ".join(atual))
            atual, tamanho = [], 0
        atual.append(frase)
        tamanho += n
    if atual:
        trechos.append(" ".join(atual))
    return trechos


def traduzir(tradutor, texto: str) -> tuple[str, int]:
    linhas, total_trechos = [], 0
    for linha in texto.split("\n"):
        if not linha.strip():
            linhas.append("")
            continue
        trechos = dividir_em_trechos(linha, tradutor.tokenizer)
        total_trechos += len(trechos)
        traducoes = tradutor(trechos, max_length=512, truncation=True)
        linhas.append(" ".join(t["translation_text"] for t in traducoes))
    return "\n".join(linhas), total_trechos
