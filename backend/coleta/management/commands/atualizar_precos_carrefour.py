from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalogo.models import Produto
from precos.models import OfertaFonte, Preco, Supermercado
from coleta.carrefour import buscar_produtos


class Command(BaseCommand):
    help = (
        "Simula ou atualiza os preços do Carrefour por correspondência exata de EAN."
    )

    def add_arguments(self, parser):
        parser.add_argument("--termo", default="arroz")
        parser.add_argument("--ean", help="Consulta um único produto pelo EAN exato.")
        parser.add_argument(
            "--todos",
            action="store_true",
            help="Percorre as ofertas ativas do Carrefour já cadastradas.",
        )
        parser.add_argument("--quantidade", type=int, default=15)
        parser.add_argument("--gravar", action="store_true")

    def handle(self, *args, **options):
        ean_alvo = str(options["ean"] or "").strip()
        todos = options["todos"]
        gravar = options["gravar"]

        if todos and ean_alvo:
            raise CommandError("Use --todos ou --ean, não os dois juntos.")

        if ean_alvo and not ean_alvo.isdigit():
            raise CommandError("O EAN deve conter apenas números.")

        if not 1 <= options["quantidade"] <= 50:
            raise CommandError("A quantidade deve estar entre 1 e 50.")

        supermercado = Supermercado.objects.filter(
            nome__iexact="Carrefour"
        ).first()

        if supermercado is None:
            raise CommandError(
                "Carrefour não está cadastrado em Supermercado."
            )

        if ean_alvo and not Produto.objects.filter(
            codigo_barras=ean_alvo
        ).exists():
            raise CommandError(
                f"EAN {ean_alvo} não está cadastrado no catálogo. "
                "Nenhuma alteração foi feita no banco."
            )

        if todos:
            ofertas = list(
                OfertaFonte.objects.filter(
                    supermercado=supermercado,
                    ativo=True,
                )
                .select_related("produto")
                .order_by("produto_id")
            )
            if not ofertas:
                self.stdout.write("Nenhuma oferta ativa do Carrefour encontrada.")
                return

            tarefas = [
                (oferta.produto.codigo_barras, oferta.produto_id)
                for oferta in ofertas
            ]
            self.stdout.write(
                f"Ofertas ativas do Carrefour: {len(tarefas)}"
            )
        else:
            termo = ean_alvo or options["termo"]
            quantidade = 1 if ean_alvo else options["quantidade"]
            tarefas = [(termo, None)]

        modo = "GRAVAÇÃO AUTORIZADA" if gravar else "SIMULAÇÃO"
        self.stdout.write(self.style.NOTICE(f"Modo: {modo}"))

        contadores = {
            "consultados": 0,
            "encontrados": 0,
            "sem_correspondencia": 0,
            "indisponiveis": 0,
            "erros": 0,
            "ofertas_criadas": 0,
            "precos_criados": 0,
            "sem_alteracao": 0,
        }

        eans_processados = set()

        for termo_busca, produto_esperado_id in tarefas:
            try:
                resultados = buscar_produtos(
                    termo=termo_busca,
                    quantidade=1 if todos or ean_alvo else options["quantidade"],
                )
            except Exception as erro:
                contadores["erros"] += 1
                self.stdout.write(self.style.WARNING(
                    f"ERRO NA BUSCA | {termo_busca} | {erro}"
                ))
                continue

            for item in resultados:
                if item.get("erro"):
                    contadores["erros"] += 1
                    self.stdout.write(self.style.WARNING(
                        f"ERRO | {item.get('url', '')} | {item['erro']}"
                    ))
                    continue

                ean = str(item.get("codigo_barras") or "").strip()
                nome = str(item.get("nome") or "").strip()
                contadores["consultados"] += 1

                if not ean or ean in eans_processados:
                    if ean:
                        self.stdout.write(f"EAN repetido ignorado: {ean}")
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Produto sem EAN ignorado: {nome}"
                        ))
                    continue

                eans_processados.add(ean)

                if produto_esperado_id is not None:
                    oferta_alvo = next(
                        (
                            oferta for oferta in ofertas
                            if oferta.produto_id == produto_esperado_id
                        ),
                        None,
                    )
                    if oferta_alvo is None or ean != str(
                        oferta_alvo.produto.codigo_barras
                    ):
                        self.stdout.write(self.style.WARNING(
                            f"EAN divergente | Esperado "
                            f"{oferta_alvo.produto.codigo_barras if oferta_alvo else 'N/A'}"
                            f" | Encontrado {ean} | {nome}"
                        ))
                        continue

                try:
                    preco = Decimal(str(item.get("preco")))
                except (InvalidOperation, TypeError, ValueError):
                    self.stdout.write(self.style.WARNING(
                        f"PREÇO INVÁLIDO | EAN {ean} | {nome}"
                    ))
                    continue

                if not preco.is_finite() or preco <= 0:
                    self.stdout.write(self.style.WARNING(
                        f"PREÇO INVÁLIDO | EAN {ean} | {nome}"
                    ))
                    continue

                produto = Produto.objects.filter(codigo_barras=ean).first()

                if produto is None:
                    contadores["sem_correspondencia"] += 1
                    self.stdout.write(
                        f"EAN NÃO CADASTRADO | {ean} | {nome} | R$ {preco:.2f}"
                    )
                    continue

                contadores["encontrados"] += 1

                if item.get("disponivel") is not True:
                    contadores["indisponiveis"] += 1
                    self.stdout.write(self.style.WARNING(
                        f"INDISPONÍVEL | Produto {produto.id} | EAN {ean}"
                    ))
                    continue

                ofertas_produto = OfertaFonte.objects.filter(
                    produto=produto,
                    supermercado=supermercado,
                ).order_by("id")

                oferta = ofertas_produto.filter(ativo=True).first()
                if oferta is None:
                    oferta = ofertas_produto.first()

                if oferta is not None and not oferta.ativo:
                    self.stdout.write(self.style.WARNING(
                        f"OFERTA INATIVA | Produto {produto.id} | "
                        f"EAN {ean} | não será reativada"
                    ))
                    continue

                if oferta is None:
                    self.stdout.write(
                        f"NOVA OFERTA | Produto {produto.id} | EAN {ean} "
                        f"| {produto.nome} | R$ {preco:.2f}"
                    )
                    if gravar:
                        with transaction.atomic():
                            oferta = OfertaFonte.objects.create(
                                produto=produto,
                                supermercado=supermercado,
                                codigo_externo=str(item.get("sku") or ""),
                                nome_externo=nome,
                                url_fonte=str(item.get("url") or ""),
                                ativo=True,
                            )
                            Preco.objects.create(
                                oferta_fonte=oferta,
                                valor=preco,
                                data_hora_coleta=timezone.now(),
                            )
                        contadores["ofertas_criadas"] += 1
                        contadores["precos_criados"] += 1
                    continue

                ultimo_preco = Preco.objects.filter(
                    oferta_fonte=oferta
                ).order_by("-data_hora_coleta", "-id").first()

                if ultimo_preco is not None and ultimo_preco.valor == preco:
                    contadores["sem_alteracao"] += 1
                    self.stdout.write(
                        f"SEM ALTERAÇÃO | Produto {produto.id} | "
                        f"EAN {ean} | R$ {preco:.2f}"
                    )
                    continue

                anterior = (
                    f"R$ {ultimo_preco.valor:.2f}"
                    if ultimo_preco is not None else "sem histórico"
                )
                self.stdout.write(
                    f"NOVO PREÇO | Produto {produto.id} | EAN {ean} "
                    f"| {anterior} -> R$ {preco:.2f}"
                )

                if gravar:
                    with transaction.atomic():
                        Preco.objects.create(
                            oferta_fonte=oferta,
                            valor=preco,
                            data_hora_coleta=timezone.now(),
                        )
                    contadores["precos_criados"] += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Resumo da execução"))
        self.stdout.write(f"Produtos consultados: {contadores['consultados']}")
        self.stdout.write(f"Correspondências por EAN: {contadores['encontrados']}")
        self.stdout.write(f"EANs não cadastrados: {contadores['sem_correspondencia']}")
        self.stdout.write(f"Indisponíveis: {contadores['indisponiveis']}")
        self.stdout.write(f"Erros de consulta: {contadores['erros']}")
        self.stdout.write(f"Ofertas criadas: {contadores['ofertas_criadas']}")
        self.stdout.write(f"Preços gravados: {contadores['precos_criados']}")
        self.stdout.write(f"Preços sem alteração: {contadores['sem_alteracao']}")

        if not gravar:
            self.stdout.write(self.style.WARNING(
                "SIMULAÇÃO: nenhuma alteração foi gravada no banco."
            ))