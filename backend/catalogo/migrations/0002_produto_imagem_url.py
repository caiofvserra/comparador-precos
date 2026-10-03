from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogo", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="imagem_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]