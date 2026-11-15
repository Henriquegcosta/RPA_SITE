
"""Integração com a API FalaZuki."""

import json
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

URL = "https://api.falazuki.com/v1/calc/net-salary"


class FalhaTributaria(Exception):
    pass


def consultar(bruto, dependentes=0, data=None):
    parametros = {
        "gross_salary": str(bruto),
        "dependents": int(dependentes)
    }

    if data:
        parametros["reference_date"] = data

    url = URL + "?" + urlencode(parametros)

    try:
        requisicao = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "PaoDOuroRH-Demo/1.0"
            }
        )

        with urlopen(requisicao, timeout=12) as resposta:
            dados = json.load(resposta)

    except (HTTPError, URLError, TimeoutError, ValueError) as erro:
        raise FalhaTributaria(
            "Não foi possível consultar a API FalaZuki"
        ) from erro

    try:
        if not isinstance(dados, dict):
            raise ValueError("Resposta não é um objeto JSON")

        answer = dados["answer"]
        breakdown = dados["breakdown"]

        valores = {
            item["key"]: Decimal(str(item["value"]))
            for item in breakdown
        }

        bruto_api = valores["gross_salary"]
        inss = abs(valores["inss"])
        irrf = abs(valores["irrf"])
        liquido = Decimal(str(answer["value"]))

        bruto_enviado = Decimal(str(bruto))

        if (
            abs(bruto_api - bruto_enviado) > Decimal("0.01")
            or inss < 0
            or irrf < 0
            or liquido < 0
            or abs(bruto_api - inss - irrf - liquido)
            > Decimal("0.02")
        ):
            raise ValueError("Valores tributários inconsistentes")

        return {
            "inss": inss,
            "irrf": irrf,
            "liquido_api": liquido
        }

    except (
        KeyError, TypeError, ValueError,
        InvalidOperation, AttributeError
    ) as erro:
        raise FalhaTributaria(
            "A API retornou dados inválidos ou inconsistentes"
        ) from erro
