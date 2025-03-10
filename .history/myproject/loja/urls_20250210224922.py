from django.contrib import admin
from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views



# Register your models here.

urlpatterns = [
    path('', login_view, name="login_view"),
    path('menu', menu, name="menu"),
    
    path('servicos', servicos, name="servicos"),
    path('caixa_compra', caixa_view_compra, name="caixa_compra"),
    path('contas_receber', contas_receber, name="contas_receber"),
    path('contas_pagar', contas_pagar, name="contas_pagar"),
    path('cadastrar_produtos', cadastrar_produtos, name="cadastrar_produtos"),
    path('cadastrar_fornecedor', cadastrar_fornecedor, name="cadastrar_fornecedor"),
    path('cadastrar_cliente', cadastrar_cliente, name="cadastrar_cliente"),
    path('cadastro_profissionais', cadastro_profissionais, name='cadastro_profissionais'),
    path('cadastro_veiculos', cadastro_veiculos, name='cadastro_veiculos'),

    path('controle_estoque', controle_estoque, name="controle_estoque"),
    path('controle_servico', controle_servico, name="controle_servico"),
    path('dashboard', dashboard, name="dashboard"),

    path('rel_cliente', rel_cliente, name='rel_cliente'),
    path('rel_fornecedor', rel_fornecedor, name='rel_fornecedor'),
    path('rel_produto', rel_produto, name='rel_produto'),
    path('rel_veiculo', rel_veiculo, name='rel_veiculo'),
    path('rel_funcionario', rel_funcionario, name='rel_funcionario'),
    path('rel_servico', rel_servico, name='rel_servico'),
    
    path('os_por_cliente/<str:cnpj>', os_por_cliente, name='os_por_cliente'),
    path('compra_por_fornecedor/<str:cnpj>', compra_por_fornecedor, name='compra_por_fornecedor'),
    path('servicos_por_veiculo/<str:placa>', servicos_por_veiculo, name='servicos_por_veiculo'),
    
    path('folha_pagamento', folha_pagamento, name='folha_pagamento'),

    # path('caiCaixa_compraxa_venda', caixa_view_venda, name="caixa_venda"),
    # path('adicionar_carrinho', adicionar_carrinho, name="adicionar_carrinho"),
    # path('remover_carrinho', remover_carrinho, name="remover_carrinho"),
    # path('finalizar_venda', finalizar_venda, name="finalizar_venda"),
    
    # path('adicionar_carrinho_compra', adicionar_carrinho_compra, name="adicionar_carrinho_compra"),
    # path('remover_carrinho_compra', remover_carrinho_compra, name="remover_carrinho_compra"),
    # path('finalizar_compra', finalizar_compra, name="finalizar_compra"),

    # # path('cadastrar_item', cadastrar_item, name="cadastrar_item"),
    # # path('atualiza_produto', atualiza_produto, name="atualiza_produto"),

    

    # path('contas_receber/<str:filtro>/<str:ordenar_por>/<str:data_inicial>/<str:data_final>/', contas_receber, name='contas_receber_sem_caixa'),
    # path('contas_receber/<int:id_caixa>/<str:filtro>/<str:ordenar_por>/<str:data_inicial>/<str:data_final>/', contas_receber, name="contas_receber"),
    # path('quant_parcela', quant_parcela, name="quant_parcela"),
    # path('nova_parcela', nova_parcela, name="nova_parcela"),
    
    # path('contas_pagar/<str:filtro>/<str:ordenar_por>/<str:data_inicial>/<str:data_final>/', contas_pagar, name='contas_pagar_sem_caixa'),
    # path('contas_pagar/<int:id_caixa>/<str:filtro>/<str:ordenar_por>/<str:data_inicial>/<str:data_final>/', contas_pagar, name="contas_pagar"),
    # path('quant_parcela_pagar', quant_parcela_pagar, name="quant_parcela_pagar"),
    # path('nova_parcela_pagar', nova_parcela_pagar, name="nova_parcela_pagar"),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

]
