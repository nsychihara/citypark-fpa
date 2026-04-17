from django.contrib import admin

from .models import Estacionamento, Fiscal, Multa, Pagamento, Usuario, Vaga, Veiculo


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'email', 'pontos', 'criado_em']
    search_fields = ['nome', 'email']


@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ['id', 'placa', 'modelo', 'cor', 'usuario']
    list_filter = ['cor']
    search_fields = ['placa', 'modelo', 'usuario__nome']


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = ['id', 'numero', 'rua', 'regiao', 'preco_hora', 'status']
    list_filter = ['status', 'regiao']
    search_fields = ['numero', 'rua', 'regiao']


@admin.register(Estacionamento)
class EstacionamentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'veiculo', 'vaga', 'hora_inicio', 'hora_fim', 'status']
    list_filter = ['status']
    search_fields = ['veiculo__placa', 'vaga__rua', 'vaga__numero']


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'estacionamento',
        'valor',
        'tempo_comprado',
        'forma_pagamento',
        'data_pagamento',
    ]
    list_filter = ['forma_pagamento']


@admin.register(Fiscal)
class FiscalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nome', 'login']
    search_fields = ['nome', 'login']


@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ['id', 'estacionamento', 'fiscal', 'valor', 'data_multa', 'status']
    list_filter = ['status']
