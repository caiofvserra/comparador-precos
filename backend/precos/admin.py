from django.contrib import admin

from .models import OfertaFonte, Preco


@admin.register(OfertaFonte)
class OfertaFonteAdmin(admin.ModelAdmin):
    list_display = ["nome_externo", "produto", "supermercado", "ativo"]
    list_filter = ["supermercado", "ativo"]
    search_fields = ["nome_externo", "produto__nome", "codigo_externo"]


@admin.register(Preco)
class PrecoAdmin(admin.ModelAdmin):
    list_display = ["oferta_fonte", "valor", "data_hora_coleta"]
    list_filter = ["oferta_fonte__supermercado"]
    date_hierarchy = "data_hora_coleta"
