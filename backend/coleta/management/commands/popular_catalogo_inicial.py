"""Preenche categorias essenciais com ofertas reais sem travar o servidor.

O catálogo inicial é pequeno e a operação pode ser repetida: cada categoria
com produtos e preços suficientes é ignorada nas próximas inicializações.
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
MINIMO_POR_TERMO = 3


def produtos_com_preco_savegnago(termo):
    return (
        Produto.objects.filter(
            nome__icontains=termo,
            ofertas__supermercado__nome__iexact="Savegnago",
            ofertas__precos__isnull=False,
        )
        .distinct()
        .count()
    )


class Command(BaseCommand):
    help = "Coleta uma pequena amostra real por categoria no Savegnago."

    def handle(self, *args, **options):
        self.stdout.write(
            f"[bootstrap] Catálogo atual: {Produto.objects.count()} produtos."
        )
        for termo in TERMOS_INICIAIS:
            existentes = produtos_com_preco_savegnago(termo)
            if existentes >= MINIMO_POR_TERMO:
                self.stdout.write(
                    f"[bootstrap] {termo}: {existentes} itens com preço, já atendido."
                )
                continue

            self.stdout.write(f"[bootstrap] Consultando Savegnago: {termo}")
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
                self.stderr.write(
                    self.style.ERROR(
                        f"[bootstrap] Falha ao importar {termo}: {erro}"
                    )
                )

        produtos = Produto.objects.count()
        precos = Preco.objects.count()
        supermercados = Supermercado.objects.count()
        self.stdout.write(
            f"[bootstrap] Final: {produtos} produtos, "
            f"{supermercados} supermercados, {precos} registros de preços."
        )

        pendentes = [
            termo
            for termo in TERMOS_INICIAIS
            if produtos_com_preco_savegnago(termo) < MINIMO_POR_TERMO
        ]
        if pendentes:
            self.stderr.write(
                self.style.WARNING(
                    "[bootstrap] Categorias com poucos produtos: "
                    + ", ".join(pendentes)
                )
            )
        if produtos == 0 or precos == 0:
            self.stderr.write(
                self.style.ERROR(
                    "[bootstrap] Nenhuma oferta real cadastrada; "
                    "verifique a disponibilidade do Savegnago."
                )
            )
