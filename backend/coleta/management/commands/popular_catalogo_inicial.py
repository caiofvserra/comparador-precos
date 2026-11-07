"""Popula uma base vazia com uma amostra pequena de ofertas reais.

Não cria dados fictícios e não bloqueia o servidor web. O comando pode ser
executado novamente: o importador reutiliza produtos por EAN e grava histórico
somente quando o preço muda.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from catalogo.models import Produto, Supermercado
from precos.models import Preco


TERMOS_INICIAIS = (
    "arroz",
    "feijão",
    "leite",
    "café",
    "macarrão",
    "detergente",
)
LIMITE_MINIMO = 20


class Command(BaseCommand):
    help = "Preenche um catálogo inicial limitado com produtos reais do Savegnago."

    def handle(self, *args, **options):
        produtos_antes = Produto.objects.count()
        if produtos_antes >= LIMITE_MINIMO and Preco.objects.count() >= LIMITE_MINIMO:
            self.stdout.write(
                f"[bootstrap] Catálogo já tem {produtos_antes} produtos; "
                "nenhuma coleta inicial necessária."
            )
            return

        self.stdout.write(
            f"[bootstrap] Iniciando coleta do Savegnago; "
            f"produtos atuais: {produtos_antes}."
        )
        for termo in TERMOS_INICIAIS:
            if (Produto.objects.count() >= LIMITE_MINIMO and Preco.objects.count() >= LIMITE_MINIMO):
                break

            self.stdout.write(f"[bootstrap] Consultando: {termo}")
            try:
                call_command(
                    "importar_savegnago",
                    termo=termo,
                    quantidade=12,
                    cep="14010000",
                    gravar=True,
                    stdout=self.stdout,
                    stderr=self.stderr,
                )
            except Exception as erro:
                # Falhas da fonte externa não devem impedir o site de subir.
                self.stderr.write(
                    self.style.ERROR(
                        f"[bootstrap] Falha ao importar {termo}: {erro}"
                    )
                )

        produtos_depois = Produto.objects.count()
        precos = Preco.objects.count()
        supermercados = Supermercado.objects.count()
        self.stdout.write(
            f"[bootstrap] Final: {produtos_depois} produtos, "
            f"{supermercados} supermercados, {precos} registros de preços."
        )
        if produtos_depois == 0 or precos == 0:
            self.stderr.write(
                self.style.ERROR(
                    "[bootstrap] Nenhuma oferta real foi cadastrada; "
                    "verifique a disponibilidade da fonte Savegnago."
                )
            )
