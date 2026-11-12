from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("coleta", "0001_execucaocoleta"),
    ]

    operations = [
        migrations.AddField(
            model_name="execucaocoleta",
            name="ultima_atividade_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
