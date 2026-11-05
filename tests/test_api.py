import os

import pytest
from fastapi.testclient import TestClient

from app import service
from app.main import app


class TokenizerFalso:
    def tokenize(self, texto):
        return texto.split()


class TradutorFalso:
    tokenizer = TokenizerFalso()

    def __call__(self, trechos, **kwargs):
        return [{"translation_text": f"FR({t})"} for t in trechos]


@pytest.fixture
def client():
    app.state.tradutor = TradutorFalso()
    return TestClient(app)


def test_health(client):
    assert client.get("/health").json()["modelo"] == "Helsinki-NLP/opus-mt-en-fr"


def test_traduz_frase_curta(client):
    corpo = client.post("/traduzir", json={"texto": "Hello world."}).json()
    assert corpo["traducao"] == "FR(Hello world.)"
    assert corpo["trechos"] == 1


def test_texto_longo_e_dividido_em_trechos():
    texto = " ".join(f"Sentence number {i} has some words." for i in range(100))
    trechos = service.dividir_em_trechos(texto, TokenizerFalso(), limite=50)
    assert len(trechos) > 1
    assert all(len(t.split()) <= 50 for t in trechos)
    assert " ".join(trechos) == texto


def test_paragrafos_sao_preservados(client):
    corpo = client.post("/traduzir", json={"texto": "First line.\n\nSecond line."}).json()
    assert corpo["traducao"] == "FR(First line.)\n\nFR(Second line.)"


@pytest.mark.parametrize("corpo", [{}, {"texto": ""}, {"texto": "x" * 10001}])
def test_entradas_invalidas(client, corpo):
    assert client.post("/traduzir", json=corpo).status_code == 422


@pytest.mark.skipif(os.getenv("RODAR_MODELO_REAL") != "1", reason="define RODAR_MODELO_REAL=1 para usar o modelo de verdade")
def test_modelo_real():
    with TestClient(app) as client:
        corpo = client.post("/traduzir", json={"texto": "Good morning, my friend."}).json()
    assert "bonjour" in corpo["traducao"].lower()
