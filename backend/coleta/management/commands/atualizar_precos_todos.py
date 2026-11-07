from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Atualiza os preços das três redes integradas em uma única execução."

    def add_arguments(self, parser):
        parser.add_argument("--cep", default="14010000")
        parser.add_argument(
            "--gravar",
            action="store_true",
            help="Grava novos preços no banco; sem a opção, executa em simulação.",
        )

    def handle(self, *args, **options):
        cep = options["cep"]
        gravar = options["gravar"]

        comandos = [
            ("Savegnago", "atualizar_precos_savegnago", {"cep": cep}),
            ("Atacadão", "atualizar_precos_atacadao", {"cep": cep}),
            ("Carrefour", "atualizar_precos_carrefour", {"todos": True}),
        ]

        falhas = []

        for nome, comando, kwargs in comandos:
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE(f"=== {nome} ==="))
            try:
                call_command(comando, gravar=gravar, **kwargs)
            except Exception as erro:
                falhas.append((nome, erro))
                self.stderr.write(
                    self.style.ERROR(f"Falha ao atualizar {nome}: {erro}")
                )

        if falhas:
            nomes = ", ".join(nome for nome, _ in falhas)
            self.stderr.write(
                self.style.WARNING(
                    f"Atualização concluída com falhas em: {nomes}."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Atualização das três redes concluída.")
            )
