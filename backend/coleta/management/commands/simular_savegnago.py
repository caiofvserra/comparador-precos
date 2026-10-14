from decimal import Decimal, InvalidOperation

import requests
from django.core.management.base import BaseCommand

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte
from coleta.savegnago import buscar_produtos


class Command(BaseCommand):
    help = "Simula a importação do Savegnago sem gravar no banco."

    def add_arguments(self, parser):
        parser.add_argument("--termo", default="leite")
        parser.add_argument("--quantidade", type=int, default=5)
        parser.add_argument("--cep", default="14010000")

    def handle(self, *args, **options):
        termo = options["termo"]
        quantidade = options["quantidade"]
        cep = "".join(c for c in options["cep"] if c.isdigit())

        if len(cep) != 8:
            self.stderr.write(
                self.style.ERROR("Informe um CEP válido com 8 dígitos.")
            )
            return

        if not 1 <= quantidade <= 50:
            self.stderr.write(
                self.style.ERROR("A quantidade deve estar entre 1 e 50.")
            )
            return


        self.stdout.write("Consultando produtos no Savegnago...")

        try:
            produtos = buscar_produtos(
                termo=termo,
                quantidade=quantidade,
                cep=cep,
            )
        except (requests.RequestException, ValueError) as erro:
            self.stderr.write(
                self.style.ERROR(f"Falha na consulta: {erro}")
            )
            return

        supermercado = Supermercado.objects.filter(
            nome__iexact="Savegnago"
        ).first()

        self.stdout.write("")
        self.stdout.write(self.style.WARNING(
            "MODO SIMULAÇÃO: nenhum dado será gravado."
        ))

        if supermercado:
            self.stdout.write(
                f"Supermercado: {supermercado.nome} (ID {supermercado.id})"
            )
        else:
            self.stdout.write(
                self.style.ERROR("Savegnago não está cadastrado no banco.")
            )

        contagem = {
            "total": len(produtos),
            "ean_invalido": 0,
            "indisponivel": 0,
            "produto_nao_encontrado": 0,
            "oferta_existente": 0,
            "preco_invalido": 0,
            "pronto_para_importar": 0,
        }

        for item in produtos:
            self.stdout.write("-" * 60)
            self.stdout.write(f"Produto: {item['nome']}")
            self.stdout.write(f"Marca: {item['marca']}")
            self.stdout.write(
                f"EAN: {item['codigo_barras'] or '(sem EAN)'}"
            )
            self.stdout.write(f"Preço informado: {item['preco']}")
            self.stdout.write(f"Disponível: {item['disponivel']}")

            ean = (item.get("codigo_barras") or "").strip()

            if (
                not ean
                or not ean.isdigit()
                or len(ean) not in (8, 12, 13, 14)
            ):
                contagem["ean_invalido"] += 1
                self.stdout.write(self.style.WARNING(
                    "Resultado: ignorar — EAN ausente ou inválido."
                ))
                continue

            if not item.get("disponivel"):
                contagem["indisponivel"] += 1
                self.stdout.write(self.style.WARNING(
                    "Resultado: ignorar — produto indisponível na fonte."
                ))
                continue

            try:
                preco = Decimal(str(item["preco"]))
                if not preco.is_finite() or preco <= 0:
                    raise InvalidOperation
            except (InvalidOperation, TypeError, ValueError):
                contagem["preco_invalido"] += 1
                self.stdout.write(self.style.WARNING(
                    "Resultado: ignorar — preço ausente ou inválido."
                ))
                continue

            produto = Produto.objects.filter(
                codigo_barras=ean
            ).first()

            if not produto:
                contagem["produto_nao_encontrado"] += 1
                self.stdout.write(self.style.WARNING(
                    "Resultado: revisar — produto não encontrado no catálogo."
                ))
                continue

            self.stdout.write(
                f"Produto correspondente: {produto.nome} (ID {produto.id})"
            )

            if supermercado is None:
                self.stdout.write(self.style.WARNING(
                    "Resultado: revisar — cadastre o supermercado."
                ))
                continue

            oferta = OfertaFonte.objects.filter(
                produto=produto,
                supermercado=supermercado,
                ativo=True,
            ).first()

            if oferta:
                contagem["oferta_existente"] += 1
                self.stdout.write(self.style.WARNING(
                    f"Resultado: revisar — oferta ativa já existe (ID {oferta.id})."
                ))
                continue

            contagem["pronto_para_importar"] += 1
            self.stdout.write(self.style.SUCCESS(
                f"Resultado: candidato à importação — R$ {preco:.2f}"
            ))

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("RESUMO DA SIMULAÇÃO")
        self.stdout.write(f"Produtos consultados: {contagem['total']}")
        self.stdout.write(f"EAN ausente ou inválido: {contagem['ean_invalido']}")
        self.stdout.write(f"Produtos indisponíveis: {contagem['indisponivel']}")
        self.stdout.write(
            f"Produtos não encontrados no catálogo: "
            f"{contagem['produto_nao_encontrado']}"
        )
        self.stdout.write(
            f"Ofertas ativas já existentes: {contagem['oferta_existente']}"
        )
        self.stdout.write(f"Preços inválidos: {contagem['preco_invalido']}")
        self.stdout.write(
            f"Candidatos à importação: {contagem['pronto_para_importar']}"
        )
        self.stdout.write("Nenhuma alteração foi feita no banco de dados.")
