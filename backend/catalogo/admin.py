from django.contrib import admin

from .models import Categoria, Produto, Supermercado


@admin.register(Supermercado)
class SupermercadoAdmin(admin.ModelAdmin):
    list_display = ["nome", "cidade", "estado", "ativo"]
    list_filter = ["ativo", "cidade"]
    search_fields = ["nome"]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ["nome"]


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ["nome", "marca", "codigo_barras"]
    search_fields = ["nome", "marca", "codigo_barras"]
    filter_horizontal = ["categorias"]
