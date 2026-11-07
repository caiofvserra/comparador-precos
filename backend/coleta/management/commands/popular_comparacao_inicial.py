"""Primeira importação controlada para testar comparações entre redes.

Usa os importadores existentes, com EAN para identificar um mesmo produto.
Não cria ofertas ou preços fictícios quando o supermercado não responde.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Count

from catalogo.models import Produto, Supermercado
from precos.models import OfertaFonte, Preco


TERMOS_ATACADAO = ("arroz", "leite", "café")
TERMOS_CARREFOUR = ("arroz", "feijão", "leite", "café", "macarrão", "detergente")
TERMOS_CARREFOUR_ESPECIFICOS = ("broto legal", "ypê", "pilão", "galo", "renata")
CEP_REFERENCIA = "14010000"
LIMITE_POR_CONSULTA = 10
LIMITE_CARREFOUR = 30
LIMITE_CARREFOUR_ESPECIFICO = 10
MINIMO_POR_TERMO = 3


def quantidade_com_preco(supermercado, termo):
    return (
        OfertaFonte.objects.filter(
            supermercado__nome__iexact=supermercado,
            ativo=True,
            precos__isnull=False,
            produto__nome__icontains=termo,
        )
        .values("produto_id")
        .distinct()
        .count()
    )


class Command(BaseCommand):
    help = (
        "Consulta amostras do Atacadão e Carrefour, preservando somente "
        "preços reais e correspondências por EAN."
    )

    def handle(self, *args, **options):
        if not Produto.objects.filter(
            ofertas__supermercado__nome__iexact="Savegnago",
            ofertas__precos__isnull=False,
        ).exists():
            self.stderr.write(
                self.style.WARNING(
                    "[comparacao] Sem catálogo Savegnago com preço; "
                    "importação multimercado não iniciada."
                )
            )
            return

        self.stdout.write("[comparacao] Iniciando coleta limitada do Atacadão.")
        for termo in TERMOS_ATACADAO:
            encontrados = quantidade_com_preco("Atacadão", termo)
            if encontrados >= MINIMO_POR_TERMO:
                self.stdout.write(
                    f"[comparacao] Atacadão {termo}: {encontrados} "
                    "produtos com preço; não precisa consultar."
                )
                continue
            try:
                call_command(
                    "importar_atacadao",
                    termo=termo,
                    quantidade=LIMITE_POR_CONSULTA,
                    cep=CEP_REFERENCIA,
                    gravar=True,
                    stdout=self.stdout,
                    stderr=self.stderr,
                )
            except Exception as erro:
                self.stderr.write(
                    self.style.WARNING(
                        f"[comparacao] Falha na consulta Atacadão {termo}: {erro}"
                    )
                )

            # Se a primeira consulta não cadastrou uma oferta sequer,
            # evita insistir em uma fonte possivelmente indisponível.
            if not OfertaFonte.objects.filter(
                supermercado__nome__iexact="Atacadão"
            ).exists():
                self.stderr.write(
                    self.style.WARNING(
                        "[comparacao] Atacadão sem ofertas consultáveis; "
                        "demais termos adiados."
                    )
                )
                break

        self.stdout.write("[comparacao] Iniciando coleta limitada do Carrefour.")
        for termo in TERMOS_CARREFOUR:
            encontrados = quantidade_com_preco("Carrefour", termo)
            if encontrados >= MINIMO_POR_TERMO:
                self.stdout.write(
                    f"[comparacao] Carrefour {termo}: {encontrados} "
                    "produtos com preço; não precisa consultar."
                )
                continue
            try:
                call_command(
                    "atualizar_precos_carrefour",
                    termo=termo,
                    quantidade=LIMITE_CARREFOUR,
                    gravar=True,
                    stdout=self.stdout,
                    stderr=self.stderr,
                )
            except Exception as erro:
                self.stderr.write(
                    self.style.WARNING(
                        f"[comparacao] Falha na consulta Carrefour {termo}: {erro}"
                    )
                )

        # Busca marcas populares para aumentar a interseção entre lojas.
        # O importador só grava preços de EANs presentes no catálogo.
        for termo in TERMOS_CARREFOUR_ESPECIFICOS:
            try:
                call_command(
                    "atualizar_precos_carrefour",
                    termo=termo,
                    quantidade=LIMITE_CARREFOUR_ESPECIFICO,
                    gravar=True,
                    stdout=self.stdout,
                    stderr=self.stderr,
                )
            except Exception as erro:
                self.stderr.write(
                    self.style.WARNING(
                        f"[comparacao] Falha na busca específica Carrefour {termo}: {erro}"
                    )
                )

        ofertas = (
            OfertaFonte.objects.filter(
                ativo=True,
                precos__isnull=False,
                supermercado__ativo=True,
            )
            .values("produto_id")
            .annotate(qtde_redes=Count("supermercado_id", distinct=True))
            .filter(qtde_redes__gte=2)
            .count()
        )
        self.stdout.write(
            "[comparacao] Resumo: "
            f"{Produto.objects.count()} produtos, "
            f"{Supermercado.objects.filter(ativo=True).count()} redes, "
            f"{Preco.objects.count()} preços registrados, "
            f"{ofertas} produtos com preços de pelo menos duas redes."
        )
        if ofertas == 0:
            self.stderr.write(
                self.style.WARNING(
                    "[comparacao] Nenhuma comparação multirrede validada por EAN; "
                    "não foram inventadas correspondências."
                )
            )
