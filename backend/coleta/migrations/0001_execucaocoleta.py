from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ExecucaoColeta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("estado", models.CharField(
                    choices=[
                        ("pendente", "Pendente"),
                        ("executando", "Executando"),
                        ("concluida", "Concluída"),
                        ("erro", "Erro"),
                    ],
                    default="pendente",
                    max_length=16,
                )),
                ("origem", models.CharField(default="schedule", max_length=32)),
                ("iniciada_em", models.DateTimeField(auto_now_add=True)),
                ("finalizada_em", models.DateTimeField(blank=True, null=True)),
                ("erro", models.TextField(blank=True)),
            ],
            options={"ordering": ["-iniciada_em"]},
        ),
    ]
