from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
from django.db.models import Max, Sum, F, FloatField, ExpressionWrapper
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
import win32print
import win32ui
import win32con
import matplotlib.pyplot as plt
import io
import base64, urllib
import pandas as pd


# Create your views here.

from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            nome_usuario = request.user.username
            return render(request, 'menu.html', {'nome_usuario': nome_usuario})
        else:
            return render(request, 'login.html', {'error': 'Usuário ou senha inválidos'})
    return render(request, 'login.html')

@login_required(login_url='/')
def menu(request):
    nome_usuario = request.user.username
    admin = ['romario.souza.7311@gmail.com']
    context = {'nome_usuario': nome_usuario}
    if nome_usuario in admin:
        context['admin'] = True
    else:
        context['admin'] = False
    # caixa_vendas = Caixa_venda.objects.all()
    # for caixa in caixa_vendas:
    #     if caixa.data_finalizacao is None:
    #         venda = Venda.objects.filter(caixa=caixa.caixa_aberto).first()

    #         if venda is not None:
    #             data_finalizacao = venda.data_finalizacao
    #             caixa.data_finalizacao = data_finalizacao
    #             caixa.save()

    return render(request, 'menu.html', context)

################ CAIXA VENDA
@login_required(login_url='/')
def caixa_view_venda(request, n_caixa=None, lista_caixa=None, select_produto=None):
    nome_usuario = request.user.username
    produtos = Produtos_1.objects.order_by('nome')
    forma_pg = Forma_PG.objects.order_by('nome')
    clientes = Cliente.objects.order_by('nome')
    caixa = Caixa_venda.objects.all()
    subtotal = 0
    if n_caixa:
        n_caixa = n_caixa
    else:    
        max_id = caixa.aggregate(Max('caixa_aberto'))['caixa_aberto__max']
        n_caixa = (max_id or 0) + 1
    if lista_caixa:
        for item in lista_caixa:
            subtotal += item.total  
    context = {"produtos": produtos, "n_caixa": n_caixa, "lista_caixa": lista_caixa, "subtotal": subtotal,
            "forma_pg": forma_pg, "clientes": clientes, 'nome_usuario': nome_usuario, 'select_produto': select_produto}
    return render(request, 'caixa_venda.html', context)

@login_required(login_url='/')
def adicionar_carrinho(request):
    if request.method == "POST":
        dados = request.POST.dict()
        cod_produto = dados.get('cod_produto') if dados.get('cod_produto') else ""
        n_caixa = dados.get('n_caixa')
        if cod_produto:
            lista_caixa = Caixa_venda.objects.filter(caixa_aberto=n_caixa) 
            select_produto = Produtos_1.objects.get(cod_produto=cod_produto) if Produtos_1.objects.filter(cod_produto=cod_produto) else None
            return caixa_view_venda(request, n_caixa, lista_caixa, select_produto)
        produto_id = dados.get('produto')
        quantidade = dados.get('quantidade')
        desconto = dados.get('desconto', '0.0')
        desconto = Decimal(desconto) if desconto else Decimal('0.0')
        if produto_id and quantidade: 
            quantidade = Decimal(quantidade)
            produto = Produtos_1.objects.get(id=produto_id)
            caixa, criado = Caixa_venda.objects.get_or_create(caixa_aberto=n_caixa, produto=produto, 
                                                        quantidade=quantidade, desconto=desconto, finalizado=False)
            caixa.total = (caixa.quantidade * caixa.produto.preco_venda) -  caixa.desconto
            caixa.save()
    lista_caixa = Caixa_venda.objects.filter(caixa_aberto=n_caixa) 
    return caixa_view_venda(request, n_caixa, lista_caixa)

@login_required(login_url='/')
def remover_carrinho(request):
    if request.method == "POST":
        dados = request.POST.dict()
        n_item = int(dados.get('n_item'))
        n_caixa = dados.get('n_caixa')
        lista_caixa = list(Caixa_venda.objects.filter(caixa_aberto=n_caixa))
        if lista_caixa:
            n_item_excluir = n_item-1
            lista_caixa[n_item_excluir].delete()
            lista_caixa = list(Caixa_venda.objects.filter(caixa_aberto=n_caixa))
    return caixa_view_venda(request, n_caixa, lista_caixa)


def emitir_cupom_fiscal(venda):
    # Tamanho fixo das colunas
    col_produto = 25  # 25 caracteres para o nome do produto
    col_quantidade = 8  # 8 caracteres para a quantidade
    col_valor_uni = 10  # 10 caracteres para o valor unitário
    col_total = 10  # 10 caracteres para o total

    # Cabeçalho formatado do cupom
    cupom_texto = [
        "--- CUPOM SEM VALOR FISCAL ---",
        f"Caixa: {venda.caixa}",
        f"Cliente: {venda.cliente.nome}",
        f"Data: {venda.data_finalizacao.strftime('%d/%m/%Y %H:%M')}",
        f"Forma de Pagamento: {venda.forma_pg.nome}",
        "------------------------------------------------------------------",
        "{:<25} {:>8} {:>10} {:>10}".format("Produto", "Qtd", "Val.Uni", "Total"),
        "------------------------------------------------------------------"
    ]

    # Obtendo todos os itens da venda
    itens_venda = Caixa_venda.objects.filter(caixa_aberto=venda.caixa)
    quant_itens = 0
    desconto = 0
    total_venda = 0

    for item in itens_venda:
        produto_nome = item.produto.nome[:col_produto]  # Limita o nome a 25 caracteres
        quantidade = item.quantidade
        valor_uni = item.produto.preco_venda
        total_item = quantidade * valor_uni
        quant_itens += 1
        desconto += item.desconto
        total_venda += total_item

        # Certifica que o nome do produto é preenchido até o limite de 25 caracteres
        produto_nome = produto_nome.ljust(col_produto)

        # Formata a linha para garantir alinhamento perfeito
        linha_formatada = "{:<25} {:>8.3f} {:>10.2f} {:>10.2f}".format(
            produto_nome, quantidade, valor_uni, total_item
        )
        cupom_texto.append(linha_formatada)

    # Adiciona os totais no final do cupom
    cupom_texto += [
        "------------------------------------------------------------------",
        "{:<25}      {:>8}".format("Quantidade de Produtos:", quant_itens),
        "{:<25} R$ {:>10.2f}".format("Subtotal:", total_venda),
        "{:<25} R$ {:>10.2f}".format("Desconto:", desconto),
        "{:<25} R$ {:>10.2f}".format("Total Pago:", venda.total),
        "------------------------------------------------------------------"
    ]

    # Debug: Imprimir o resultado no console (para verificação)
    for linha in cupom_texto:
        print(linha)

    # Retorna o texto do cupom
    return "\n".join(cupom_texto)



    # # Definir configurações de impressão
    # printer_name = win32print.GetDefaultPrinter()
    # hprinter = win32print.OpenPrinter(printer_name)
    # devmode = win32print.GetPrinter(hprinter, 2)["pDevMode"]
    
    # # # Configurar o papel A4 (210 x 297mm)
    # devmode.PaperSize = 9  # Tamanho A4
    # devmode.PaperWidth = 2100  # Largura em 0.1mm (210 mm)
    # devmode.PaperLength = 2970  # Altura em 0.1mm (297 mm)

    # # # Criar o DC de dispositivo de impressão
    # hdc = win32ui.CreateDC()
    # hdc.CreatePrinterDC(printer_name)
    # hdc.SetMapMode(win32con.MM_TWIPS)  # Modo de mapeamento para texto (0.01 inch)

    # # # Definir fonte (Lucida Console)
    # font = win32ui.CreateFont({
    #     "name": "Lucida Console",
    #     "height": -150,  # Tamanho da fonte (em twips)
    #     "weight": 400,  # Regular
    # })
    # hdc.SelectObject(font)

    # # # Margens e espaçamento entre linhas
    # margin_left = 0
    # line_height = 200  # Altura de cada linha (ajustável)
    # y_position = 0  # Começa do topo

    # # # Escrever o texto do cupom linha por linha
    # hdc.StartDoc("Cupom Fiscal")
    # hdc.StartPage()

    # for linha in cupom_texto:
    #     hdc.TextOut(margin_left, y_position, linha)
    #     y_position -= line_height  # Move para a próxima linha (em twips)

    # hdc.EndPage()
    # hdc.EndDoc()
    # win32print.ClosePrinter(hprinter)


@login_required(login_url='/')
def finalizar_venda(request):
    if request.method=="POST":
        nome_usuario = request.user.username
        dados = request.POST.dict()
        acao = dados.get('action')
        if acao == "excluir_item":
            n_item = int(dados.get('n_item'))
            n_caixa = dados.get('n_caixa')
            lista_caixa = list(Caixa_venda.objects.filter(caixa_aberto=n_caixa))
            if lista_caixa:
                n_item_excluir = n_item-1
                lista_caixa[n_item_excluir].delete()
                lista_caixa = list(Caixa_venda.objects.filter(caixa_aberto=n_caixa))
            return caixa_view_venda(request, n_caixa, lista_caixa)
        elif acao == "finalizar_venda":
            n_caixa = dados.get('n_caixa')	
            forma_pg_id = dados.get('forma_pg')
            obs = dados.get('obs')
            cliente_id = dados.get('cliente')
            frete = dados.get('frete')
            total = dados.get('subtotal')
            total = Decimal(total.replace(',', '.'))
            cliente = get_object_or_404(Cliente, id=cliente_id) if cliente_id else Cliente.objects.get(id=1)
            forma_pg = get_object_or_404(Forma_PG, id=forma_pg_id) if forma_pg_id else Forma_PG.objects.get(id=1)

            if n_caixa and forma_pg and total and cliente:
                if forma_pg.id not in [4, 5, 6]:
                    vencimento = timezone.now()
                    data_pg = timezone.now()
                    parcela = "1 / 1"
                else: 
                    vencimento = None
                    data_pg = None
                    parcela = ""

                caixa = Caixa_venda.objects.filter(caixa_aberto=n_caixa)
                for item in caixa:
                    item.finalizado = True
                    item.save()

                    produto = item.produto.nome
                    quantidade = item.quantidade
                    estoque = Produtos_1.objects.get(nome=produto)
                    estoque.estoque -= quantidade 
                    estoque.save()
                venda, criar = Venda.objects.get_or_create(caixa=n_caixa, usuario=nome_usuario, data_finalizacao = timezone.now(), frete=frete, 
                                                        forma_pg=forma_pg, obs=obs, cliente=cliente, total=total,
                                                        vencimento=vencimento, data_pg=data_pg, parcelas=parcela)
                 # Emitindo o cupom fiscal
                cupom = emitir_cupom_fiscal(venda)

        return caixa_view_venda(request)
        

################ CADASTROS

@login_required(login_url="/")
def cadastrar_produtos(request):
    nome_usuario = request.user.username
    produtos = Produtos_1.objects.all()
    max_id = produtos.aggregate(Max('id'))['id__max'] + 1 or 0
    marcas = Marca.objects.all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')
    uni_medida = Unidade_medida.objects.all().order_by('nome')
    id = request.POST.get('id_produto')
    context = {'max_id': max_id, 'id': id, 'marcas': marcas, 'categorias': categorias, 'uni_medida': uni_medida, 'nome_usuario': nome_usuario}
    if request.method == "POST":
        id = request.POST.get('id_produto')
        if Produtos_1.objects.filter(id=id).exists():
            produto = Produtos_1.objects.get(id=id)
            context = {'max_id': max_id, 'produto': produto, 'marcas': marcas,'id': id, 'categorias': categorias, 'uni_medida': uni_medida}
        if request.POST.get('action'):
            dados = request.POST.dict()
            imagem = request.FILES.get('imagem', None)
            nome = (dados.get('nome') or "").strip()
            categoria = Categoria.objects.get(id=dados.get('categoria')) or Categoria.objects.get(id=1)
            marca = Marca.objects.get(id=dados.get('marca')) or Marca.objects.get(id=1)
            descricao = dados.get('descricao') or ""
            preco = dados.get('preco') or "0,00"
            preco = float(preco.replace(',', '.'))
            obs = dados.get('obs') or ""
            uni_med = Unidade_medida.objects.get(id=dados.get('unidade_medida')) or Unidade_medida.objects.get(id=1)
            peso = dados.get('peso') or "0,00"
            peso = float(peso.replace(',', '.'))
            dimensoes = dados.get('dimensoes') or "0 x 0 x 0"
            cod_barras = dados.get('cod_barras') or "0"

            if Produtos_1.objects.filter(id=id).exists():
                produto = Produtos_1.objects.get(id=id)
                if imagem:
                    produto.imagem = imagem or produto.imagem  # Apenas atualize se uma nova imagem foi enviada
                produto.nome = nome or produto.nome
                produto.categoria = categoria or produto.categoria
                produto.marca = marca or produto.marca
                produto.descricao = descricao or produto.descricao
                produto.preco_venda = preco if preco is not None else produto.preco_venda
                produto.obs = obs or produto.obs
                produto.unidade_medida = uni_med
                produto.peso = peso if peso is not None else produto.peso
                produto.dimensoes = dimensoes or produto.dimensoes
                produto.codigo_barras = cod_barras or produto.codigo_barras
                produto.save()
                context['produto'] = produto
            else:
                produto = Produtos_1.objects.create(cod_produto=id, imagem=imagem, nome=nome, categoria=categoria, marca=marca, descricao=descricao,
                                                    preco_venda=preco, obs=obs, unidade_medida=uni_med, peso=peso, dimensoes=dimensoes, codigo_barras=cod_barras, usuario=nome_usuario)
                context['produto'] = produto

    return render(request, 'cadastrar_produtos.html', context)

@login_required(login_url='/')
def cadastrar_fornecedor(request):
    cnpj = request.POST.get('cnpj') if request.POST.get('cnpj') != None else ""
    nome_usuario = request.user.username        
    atividades = Atividade.objects.order_by('nome')
    context = {'cnpj': cnpj, 'nome_usuario': nome_usuario, 'atividades': atividades}
    if request.method == "POST":
        if Fornecedor.objects.filter(cnpj=cnpj).exists():
            fornecedor = Fornecedor.objects.get(cnpj=cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                fornecedor.nome = request.POST.get('nome')
                fornecedor.endereco = request.POST.get('endereco')
                fornecedor.telefone = request.POST.get('telefone')
                fornecedor.whatsapp = request.POST.get('whatsapp')
                fornecedor.email = request.POST.get('email')
                fornecedor.atividade = request.POST.get('atividade')
                fornecedor.save()
        else:
            fornecedor = Fornecedor.objects.filter(cnpj=cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                nome = request.POST.get('nome')
                endereco = request.POST.get('endereco')
                telefone = request.POST.get('telefone')
                whatsapp = request.POST.get('whatsapp')
                email = request.POST.get('email')
                atividade = request.POST.get('atividade')
                if nome and endereco and telefone and email and whatsapp and cnpj:
                    fornecedor = Fornecedor.objects.get_or_create(nome=nome, cnpj=cnpj, endereco=endereco, telefone=telefone, whatsapp=whatsapp, email=email, atividade=atividade)
                fornecedor = Fornecedor.objects.get(cnpj=cnpj)# if Fornecedor.objects.get(cnpj=cnpj).exists() else ""
        context = {
            'cnpj': cnpj,
            'nome': fornecedor.nome if fornecedor else "", 
            'endereco': fornecedor.endereco if fornecedor else "", 
            'telefone': fornecedor.telefone if fornecedor else "", 
            'whatsapp': fornecedor.whatsapp if fornecedor else "", 
            'email': fornecedor.email if fornecedor else "",
            'nome_usuario': nome_usuario,
        }
            
    return render(request, 'cadastrar_fornecedor.html', context)

@login_required(login_url='/')
def cadastrar_cliente(request):
    cnpj = request.POST.get('cnpj') if request.POST.get('cnpj') != None else ""
    nome_usuario = request.user.username
    context = {'cnpj': cnpj, 'nome_usuario':nome_usuario}

    if request.method == "POST":
        dados = request.POST.dict()
        if Cliente.objects.filter(cnpj=cnpj).exists():
            cliente = Cliente.objects.get(cnpj=cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:                
                cliente.nome = request.POST.get('nome')
                cliente.endereco = request.POST.get('endereco')
                cliente.telefone = request.POST.get('telefone')
                cliente.whatsapp = request.POST.get('whatsapp')
                cliente.email = request.POST.get('email')
                cliente.save()
        else:
            cliente = Cliente.objects.filter(cnpj=cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                nome = request.POST.get('nome')
                endereco = request.POST.get('endereco')
                telefone = request.POST.get('telefone')
                whatsapp = request.POST.get('whatsapp')
                email = request.POST.get('email')
                if nome and endereco and telefone and email and whatsapp and cnpj:
                    cliente = Cliente.objects.get_or_create(nome=nome, cnpj=cnpj, endereco=endereco, telefone=telefone, whatsapp=whatsapp, email=email)
                cliente = Cliente.objects.get(cnpj=cnpj)
        
        context = {
            'cnpj': cnpj,
            'nome': cliente.nome if cliente else "", 
            'endereco': cliente.endereco if cliente else "", 
            'telefone': cliente.telefone if cliente else "", 
            'whatsapp': cliente.whatsapp if cliente else "", 
            'email': cliente.email if cliente else "",
            'nome_usuario': nome_usuario,
        }
    return render(request, 'cadastrar_cliente.html', context)


################ CONTROLE DE ESTOQUE

@login_required(login_url='/')
def controle_estoque(request, ordenar_por="id"):
    produtos = Produtos_1.objects.all()
    compras = Caixa_compra.objects.filter(finalizado=True)
    vendas = Caixa_venda.objects.filter(finalizado=True)
    relatorio = []
    dias = 7
    dias_atras = timezone.now() - timedelta(days=7)
    if request.method == "POST":
        dias = request.POST.get('quant_vend_ult_dias')
        dias_atras = timezone.now() - timedelta(days=int(dias))
    vendas_ultimos_dias = Venda.objects.filter(data_finalizacao__gte=dias_atras)
    for item in produtos:
        custo = sum(compra.total for compra in compras if compra.produto == item)
        quant_compra = sum(compra.quantidade for compra in compras if compra.produto == item)
        if quant_compra > 0:
            med_custo = custo / quant_compra
        else:
            med_custo = 0
        quant_venda = sum(venda.quantidade for venda in vendas if venda.produto == item)
        custo_quant_prod_vendido = med_custo * quant_venda
        total_vendido = sum(venda.total for venda in vendas if venda.produto == item)
        lucro = total_vendido - custo_quant_prod_vendido
        if custo_quant_prod_vendido > 0:
            porc_lucro = lucro / custo_quant_prod_vendido * 100
        else:
            porc_lucro = 0
        quant_vendas_geral =sum(venda.quantidade for venda in vendas)
        if quant_vendas_geral == 0 or quant_venda == 0:
            porc_venda_do_item = 0
        else:
            porc_venda_do_item = quant_venda / quant_vendas_geral * 100
        valor_venda_geral = sum(venda.total for venda in vendas)
        if total_vendido == 0 or valor_venda_geral == 0:
            porc_valor_venda_do_produto = 0
        else:
            porc_valor_venda_do_produto = total_vendido / valor_venda_geral * 100

        caixa_ult_venda = Caixa_venda.objects.filter(produto=item, finalizado=True).last()
        if caixa_ult_venda:
            ultima_venda = Venda.objects.filter(caixa=caixa_ult_venda.caixa_aberto).first()
            data_ult_venda = ultima_venda.data_finalizacao if ultima_venda else ""
            if ultima_venda:
                data_ult_venda = ultima_venda.data_finalizacao.strftime('%d/%m/%Y')
            else:
                data_ult_venda = ""
        else:
            data_ult_venda = ""
        quant_vend_ult_dias = sum(
            caixa_venda.quantidade 
            for venda in vendas_ultimos_dias 
            for caixa_venda in Caixa_venda.objects.filter(produto=item, caixa_aberto=venda.caixa)
        )
        relatorio.append({
            'id': item.id,
            'produto': item.nome,
            'marca': item.marca.nome,
            'categoria': item.categoria.nome,
            'estoque': item.estoque,
            'quant_compra': quant_compra,
            'quant_venda': quant_venda,
            'lucro': lucro,
            'porc_lucro': porc_lucro,
            'porc_venda_do_item': porc_venda_do_item,
            'porc_valor_venda_do_produto': porc_valor_venda_do_produto,
            'data_ult_venda':data_ult_venda,
            'quant_vend_ult_dias': quant_vend_ult_dias,
        })
        
    if request.method == "POST":
        ordenar_por = request.POST.get('ordenar_por')
        if ordenar_por == 'produto':
            relatorio = sorted(relatorio, key=lambda x: (x.get('produto') is None, x.get('produto').lower()))
        elif ordenar_por == 'id':
            relatorio = sorted(relatorio, key=lambda x: (x.get(ordenar_por) is None, x.get(ordenar_por)), reverse=False)
        else:
            relatorio = sorted(relatorio, key=lambda x: (x.get(ordenar_por) is None, x.get(ordenar_por)), reverse=True)
    nome_usuario = request.user.username

    context = {"relatorio": relatorio,
               "ordenar_por": ordenar_por,
               "dias": dias,
               "nome_usuario": nome_usuario,
               }
    return render(request, 'controle_estoque.html', context)

def grafico_forma_pg(anos, meses):
    forma_pg = Forma_PG.objects.all()
    labels = []
    dados_grafico_rosca = []
    for item in forma_pg:
        quant = Venda.objects.filter(
            forma_pg=item,
            data_finalizacao__year__in=anos,  # Filtra por anos selecionados
            data_finalizacao__month__in=meses  # Filtra por meses selecionados
        ).count()

        if quant > 0:
            labels.append(item.nome)
            dados_grafico_rosca.append(quant)
    
    explode= [0.05] * len(dados_grafico_rosca)
    cores_personalizadas = ['#6FA0C7',  # Azul Claro 1
                            '#6BBEDC',  # Azul Claro 2
                            '#3BAFD6',  # Azul Claro 3
                            '#0094C8',  # Azul Claro 4
                            '#0077B3',  # Azul Claro 5
                            '#005FA3']  # Azul Claro 6
    plt.figure(figsize=(3, 2), facecolor='none') # polegadas do grafico
    plt.pie(dados_grafico_rosca, labels=labels, autopct='%1.0f%%', startangle=70, wedgeprops={'width': 0.7}, colors=cores_personalizadas,
            explode=explode, textprops={'fontsize': 6, 'fontweight': 'bold'})
    plt.title('')
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    grafico_forma_pg = base64.b64encode(image_png).decode('utf-8')
    return grafico_forma_pg

def grafico_vendas(anos):
    # Filtrar as vendas com data de finalização
    vendas = Venda.objects.filter(
                                  data_finalizacao__year__in=anos,
                                  )

    # Criar um dicionário para armazenar o total por mês
    total_por_mes = {}
    for venda in vendas:
        mes = venda.data_finalizacao.month  # Obter o mês da data de finalização
        if mes in total_por_mes:
            total_por_mes[mes] += venda.total  # Somar o total ao mês existente
        else:
            total_por_mes[mes] = venda.total  # Inicializar o total para o mês

    # Preparar os dados para o gráfico
    meses = sorted(total_por_mes.keys())  # Obter os meses com vendas
    totais = [total_por_mes[mes] for mes in meses]  # Total de vendas para os meses existentes

    # Criar o gráfico
    plt.figure(figsize=(10, 3))
    plt.plot(meses, totais, marker='o', color='#0077B3')

    # Configurar os rótulos dos meses para os meses que têm vendas
    nomes_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    plt.xticks(meses, [nomes_meses[m - 1] for m in meses], rotation=45)  # Ajuste para o índice de lista
    
    # Adicionar os valores acima de cada ponto
    for m, total in zip(meses, totais):
        plt.text(m, total, f'{total:,.0f}'.replace(',', '.'), ha='center', va='bottom')

    plt.grid(visible=False)
    plt.yticks([])  # Remove os valores do eixo y

    # Remover as bordas do gráfico
    for spine in plt.gca().spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    # Salvar o gráfico em um buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', transparent=True)
    buffer.seek(0)
    image_png_line = buffer.getvalue()
    buffer.close()
    grafico_vendas_mensais = base64.b64encode(image_png_line).decode('utf-8')

    return grafico_vendas_mensais

def grafico_marca(anos, meses_selecionados):
    vendas = Caixa_venda.objects.filter(
                                        data_finalizacao__year__in=anos,
                                        data_finalizacao__month__in=meses_selecionados)
    total_por_marca = {}
    for venda in vendas:
        marca = venda.produto.marca.nome
        if marca in total_por_marca:
            total_por_marca[marca] += venda.total
        else:
            total_por_marca[marca] = venda.total

    explode= [0.05] * len(total_por_marca)
    cores_personalizadas = ['#6FA0C7',  # Azul Claro 1
                            '#6BBEDC',  # Azul Claro 2
                            '#3BAFD6',  # Azul Claro 3
                            '#0094C8',  # Azul Claro 4
                            '#0077B3',  # Azul Claro 5
                            '#005FA3']  # Azul Claro 6
    plt.figure(figsize=(3, 2), facecolor='none') # polegadas do grafico
    plt.pie(list(total_por_marca.values()),  # valores para o gráfico
            labels=list(total_por_marca.keys()),  # rótulos das marcas
            autopct='%1.0f%%', 
            startangle=70, 
            wedgeprops={'width': 0.7}, 
            colors=cores_personalizadas,
            explode=explode, 
            textprops={'fontsize': 6, 'fontweight': 'bold'})

    plt.title('')
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    grafico_marca = base64.b64encode(image_png).decode('utf-8')
    return grafico_marca

def grafico_categorias(anos, meses_selecionados):
    vendas = Caixa_venda.objects.filter(data_finalizacao__year__in=anos,
                                  data_finalizacao__month__in=meses_selecionados)
    total_por_categoria = {}
    for venda in vendas:
        categoria = venda.produto.categoria.nome
        if categoria in total_por_categoria:
            total_por_categoria [categoria] += venda.total
        else:
            total_por_categoria [categoria] = venda.total

    explode = [0.05] * len(total_por_categoria)
    cores_personalizadas = [
                            '#4A90E2',  # Azul Médio
                            '#2C82C9',  # Azul Intenso
                            '#1B6FA8',  # Azul Escuro
                            '#5DADE2',  # Azul Claro Suave
                            '#3498DB',  # Azul Vibrante
                            '#2980B9',  # Azul Profundo
                            '#0E4C92',  # Azul Navy
                        ]
    
    plt.figure(figsize=(3,2), facecolor='none')              # polegadas do grafico
    plt.pie(list(total_por_categoria.values()),            # plt.pie() - clia o grafico de pizza # valores é o list(total_por_categoria.values())
            labels=list(total_por_categoria.keys()),       # rotulos das categorias
            autopct='%1.0f%%',                             # formato dos valores
            startangle=70,                                 # define o angulo inicial do grafico
            wedgeprops={'width': 0.7},                     # largura das fatias do grafico
            colors=cores_personalizadas,                   # cores
            explode=explode,
            textprops={'fontsize': 6, 'fontweight': 'bold'}
            ) 

    plt.title('')                                          # titulo
    buffer = io.BytesIO()                                  # um arquivo em memória que pode armazenar dados binários (bytes), permitindo leitura e escrita de forma similar a arquivos físicos, mas sem a necessidade de gravar no disco.



    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    grafico_categorias = base64.b64encode(image_png).decode('utf-8')
    return grafico_categorias

def grafico_quat_por_marca(anos, meses_selecionados):
    vendas = Caixa_venda.objects.filter(data_finalizacao__year__in=anos,
                                  data_finalizacao__month__in=meses_selecionados)
    quant_vendas_marca = {}
    for venda in vendas:
        marca = venda.produto.marca.nome
        if marca in quant_vendas_marca:
            quant_vendas_marca[marca] += 1
        else:
            quant_vendas_marca[marca] = 1
            

    marcas_ordenados = sorted(quant_vendas_marca.items(), key=lambda x: x[1], reverse=True)
    top_10_produtos = marcas_ordenados[:10]

    # Separa produtos e valores
    marcas = [produto for produto, total in top_10_produtos]
    valores = [total for produto, total in top_10_produtos]


    # Gerar o gráfico
    fig, ax = plt.subplots(figsize=(10,3))
    ax.bar(marcas, valores)
    # Remover o plano de fundo
    ax.patch.set_alpha(0)  # Define a transparência do fundo para 0 (remove o fundo)
    fig.patch.set_alpha(0)  # Remove o fundo da figura completa

    # Remover as bordas dos eixos
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_yticklabels([])  # Remove os rótulos do eixo Y
    ax.set_yticks([])  # Remove os ticks do eixo Y
    bars = ax.bar(marcas, valores, color='blue')

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height}', ha='center', va='bottom')


    # Converter o gráfico para formato PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)      
    buf.seek(0)
    string = base64.b64encode(buf.read())
    grafico_quat_por_marca = urllib.parse.quote(string)

    
    return grafico_quat_por_marca

def vendas_por_produto(anos, meses_selecionados):
    vendas = Caixa_venda.objects.filter(data_finalizacao__year__in=anos,
                                  data_finalizacao__month__in=meses_selecionados)
    total_por_produto = {}

    # Calcula o total por produto
    for venda in vendas:
        id = venda.produto.id
        nome = venda.produto.nome
        marca = venda.produto.marca.nome
        produto = str(id) + '-' + nome + '-' + marca

        
        # produto = venda.produto.nome
        if produto in total_por_produto:
            total_por_produto[produto] += venda.total
        else:
            total_por_produto[produto] = venda.total

    # Ordena os produtos e pega os 10 maiores
    produtos_ordenados = sorted(total_por_produto.items(), key=lambda x: x[1], reverse=True)
    top_10_produtos = produtos_ordenados[:6]

    # Separa produtos e valores
    produtos = [produto for produto, total in top_10_produtos]
    valores = [total for produto, total in top_10_produtos]

    # Cria o gráfico
    fig, ax = plt.subplots(figsize=(10, 5))  # Aumentar a largura
    ax.bar(produtos, valores, color='blue')

    ax.patch.set_alpha(0)  # Define a transparência do fundo para 0 (remove o fundo)
    fig.patch.set_alpha(0)  # Remove o fundo da figura completa

    # Remover as bordas dos eixos
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_yticklabels([])  # Remove os rótulos do eixo Y
    ax.set_yticks([])  # Remove os ticks do eixo Y

    # Adiciona os valores acima das barras
    for bar in ax.patches:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height:,.0f}'.replace(',', '.'), ha='center', va='bottom')

    # Rotacionar os rótulos do eixo X
    # ax.set_xticklabels(produtos, rotation=90, ha='center')  # Rotação de 90 graus

    ax.set_xticklabels(produtos, rotation=45, ha='right')
    plt.tight_layout()  # Ajusta automaticamente o layout

    # Converter o gráfico para formato PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)      
    buf.seek(0)
    string = base64.b64encode(buf.read())
    vendas_por_produto = urllib.parse.quote(string)    
    return vendas_por_produto

def quant_produto_vend(anos, meses_selecionados):
    vendas = Caixa_venda.objects.filter(data_finalizacao__year__in=anos,
                                  data_finalizacao__month__in=meses_selecionados)
    quant_produtos_vendidos = {}
    for venda in vendas:
        id = venda.produto.id
        nome = venda.produto.nome
        marca = venda.produto.marca.nome
        produto = str(id) + '-' + nome + '-' + marca
        if produto in quant_produtos_vendidos:
            quant_produtos_vendidos[produto] += venda.quantidade
        else:
            quant_produtos_vendidos[produto] = venda.quantidade
        
    produtos_ordenados = sorted(quant_produtos_vendidos.items(), key=lambda x: x[1], reverse=True)
    top_10_produtos = produtos_ordenados[:6]

    # Separa produtos e valores
    produtos = [produto for produto, total in top_10_produtos]
    valores = [total for produto, total in top_10_produtos]

    # Cria o gráfico
    fig, ax = plt.subplots(figsize=(10, 5))  # Aumentar a largura
    ax.bar(produtos, valores, color='blue')

    ax.patch.set_alpha(0)  # Define a transparência do fundo para 0 (remove o fundo)
    fig.patch.set_alpha(0)  # Remove o fundo da figura completa

    # Remover as bordas dos eixos
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_yticklabels([])  # Remove os rótulos do eixo Y
    ax.set_yticks([])  # Remove os ticks do eixo Y

    # Adiciona os valores acima das barras
    for bar in ax.patches:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f'{height:,.0f}'.replace(',', '.'), ha='center', va='bottom')

    # Rotacionar os rótulos do eixo X
    # ax.set_xticklabels(produtos, rotation=90, ha='center')  # Rotação de 90 graus

    ax.set_xticklabels(produtos, rotation=45, ha='right')
    plt.tight_layout()  # Ajusta automaticamente o layout

    # Converter o gráfico para formato PNG
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)      
    buf.seek(0)
    string = base64.b64encode(buf.read())
    quant_produtos_vendidos = urllib.parse.quote(string)    
    return quant_produtos_vendidos

def dashboard(request):
    nome_usuario = request.user.username
    anos = request.POST.getlist('filtro_anos')
    meses = request.POST.getlist('filtrar_meses')
    
    # Converte anos para inteiros
    anos = list(map(int, anos)) if anos else []  # Converte para inteiro se houver anos selecionados

    # Mapeia os nomes dos meses para os números
    meses_nome = {
        1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR', 5: 'MAI', 6: 'JUN',
        7: 'JUL', 8: 'AGO', 9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'
    }

    # Inverte o dicionário para mapear os nomes para os números
    meses_ordenacao = {nome_mes: num_mes for num_mes, nome_mes in meses_nome.items()}

    # Converte os meses selecionados para seus números correspondentes
    meses_selecionados = [meses_ordenacao[mes] for mes in meses if mes in meses_ordenacao]  # Aqui pegamos os números dos meses

    if not meses_selecionados:
        meses_selecionados = list(meses_nome.keys())

    meses_selecionados_nomes = [meses_nome[num] for num in meses_selecionados]

    vendas = Venda.objects.all()
    anos_vendas = []
    meses_vendas = []

    # Iterando sobre cada venda
    for venda in vendas:
        if venda.data_finalizacao:  # Verifica se a data_finalizacao não é None
            anos_vendas.append(venda.data_finalizacao.year)  # Adiciona o ano à lista
            meses_vendas.append(meses_nome[venda.data_finalizacao.month])  # Adiciona o nome do mês

    # Se você quiser ter anos e meses únicos, pode usar conjuntos (set)
    anos_unicos = list(set(anos_vendas))  # Remove anos duplicados
    meses_unicos = list(set(meses_vendas))  # Remove meses duplicados

    # Ordena os meses com base no número do mês
    meses_unicos.sort(key=lambda mes: meses_ordenacao[mes])

    # Se nenhum ano foi selecionado, use os anos disponíveis
    if not anos:
        anos = anos_unicos
    if not meses_selecionados:
        meses_selecionados = [1, 2 , 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    
    grafico_pg = grafico_forma_pg(anos, meses_selecionados)
    grafico_vendas_mensais = grafico_vendas(anos)
    grafico_total_marca = grafico_marca(anos, meses_selecionados)
    grafico_total_categoria = grafico_categorias(anos, meses_selecionados)
    grafico_quat_marca = grafico_quat_por_marca(anos, meses_selecionados)
    grafico_vendas_porduto = vendas_por_produto(anos, meses_selecionados)
    grafico_quant_prod_ved = quant_produto_vend(anos, meses_selecionados)
    context = {
        'anos': anos,
        'meses_selecionados_nomes': meses_selecionados_nomes,
        'nome_usuario': nome_usuario,
        'anos_unicos': anos_unicos,
        'meses_unicos': meses_unicos,
        'grafico_forma_pg': grafico_pg,
        'grafico_vendas_mensais': grafico_vendas_mensais,
        'grafico_total_marca': grafico_total_marca,
        'grafico_quat_marca': grafico_quat_marca,
        'grafico_total_categoria': grafico_total_categoria,
        'grafico_vendas_porduto': grafico_vendas_porduto,
        'grafico_quant_prod_ved': grafico_quant_prod_ved,
    }
    return render(request, 'dashboard.html', context)


################ RELATORIO CONTAS A RECEBER
@login_required(login_url='/')
def contas_receber(request, id_titulo=None, data_inicial=None, data_final=None, filtro='todos', ordenar_por='caixa'):#
    relatorio = []
    dados_caixa = {}
    periodo = {}
    if request.method == "POST":
        filtro = request.POST.get('titulos_pg')
        ordenar_por = request.POST.get('ordenar_por', 'caixa')
        id_titulo = request.POST.get('id_titulo')
        data_inicial = request.POST.get('data_inicial')
        data_final = request.POST.get('data_final')
        try:
            if data_inicial:
                data_inicial = datetime.strptime(data_inicial, '%d/%m/%Y').strftime('%Y-%m-%d')
            if data_final:
                data_final = datetime.strptime(data_final, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            raise ValidationError('Formato de data inválido. Use o formato dd/mm/yyyy.')
    vendas = Venda.objects.all()
    if not data_inicial:
        data_inicial = now().date()
    if not data_final:
        data_final = now().date()    
    if data_inicial and data_final:
        vendas = vendas.filter(data_finalizacao__date__range=[data_inicial, data_final])
    if filtro == "nao":
        vendas = vendas.filter(data_pg__isnull=True)
    elif filtro == "sim":
        vendas = vendas.filter(data_pg__isnull=False)
    vendas = vendas.order_by(ordenar_por)
    total_vendas = vendas.aggregate(total=Sum('total'))['total'] or 0
    quant_vendas = vendas.count()
    desconto_geral = vendas.aggregate(desconto=Sum('desconto'))['desconto'] or 0
    acrescimo_geral = vendas.aggregate(acrescimo=Sum('acrescimo'))['acrescimo'] or 0
    total_vendas = total_vendas + acrescimo_geral - desconto_geral

    for item in vendas:
        if not any(d['caixa'] == item.caixa and d['parcela'] == item.parcelas for d in relatorio):
            novo_relatorio = {
                'id': item.id,
                'caixa': item.caixa if item.caixa else "",
                'cliente': item.cliente.nome if item.cliente else "",
                'data_venda': item.data_finalizacao if item.data_finalizacao else "",
                'frete': item.frete if item.frete else "",
                'forma_pg': item.forma_pg.nome if item.forma_pg else "",
                'parcela': item.parcelas if item.parcelas else "",
                'vencimento': item.vencimento if item.vencimento else "",
                'pagamento': item.data_pg if item.data_pg else "",
                'desconto': item.desconto if item.desconto else Decimal('0.00'),
                'acrescimo': item.acrescimo if item.acrescimo else Decimal('0.00'),
                'total_pg': (item.total + item.acrescimo - item.desconto) if item.total else Decimal('0.00'),
                'obs': item.obs if item.obs else "",
            }
            relatorio.append(novo_relatorio)
    if id_titulo:
        venda = vendas.filter(id=id_titulo).first()
        if venda:
            dados_caixa = {
                'cliente': venda.cliente.nome if venda.cliente else "",
                'caixa': venda.caixa if venda.caixa else "",
                'id_caixa': id_titulo,
                'data_pg': venda.data_pg if venda.data_pg else None,
                'valor': float(venda.total) if venda.total else 0.00,
                'acrescimo': float(venda.acrescimo) if venda.acrescimo else 0.00,
                'desconto': float(venda.desconto) if venda.desconto else 0.00,
                'vencimento': venda.vencimento if venda.vencimento else None,
                'parcela': venda.parcelas if venda.parcelas else "",
                'forma_pg': venda.forma_pg.nome if venda.forma_pg else "",
                'obs': venda.obs if venda.obs else "",
            }
            dados_caixa['desconto'] = str(dados_caixa['desconto']).replace(',', '.')
            dados_caixa['acrescimo'] = str(dados_caixa['acrescimo']).replace(',','.')
            dados_caixa['valor'] = str(dados_caixa['valor']).replace(',','.')
    if request.method == "POST":
        if isinstance(data_inicial, str):
            data_inicial = data_inicial[8:10] + "/" + data_inicial[5:7] + "/" + data_inicial[:4]
        if isinstance(data_final, str):
            data_final = data_final[8:10] + "/" + data_final[5:7] + "/" + data_final[:4]
    else:
        if isinstance(data_final, date):
            data_final = data_final.strftime("%d/%m/%Y")
        if isinstance(data_inicial, date):
            data_inicial = data_inicial.strftime("%d/%m/%Y")
    periodo = {
        'data_inicial': data_inicial,
        'data_final': data_final,
    }
    nome_usuario = request.user.username
    context = {
        'relatorio': relatorio,
        'dados_caixa': dados_caixa,
        'filtro': filtro,
        'ordenar_por': ordenar_por,
        'total_vendas': total_vendas,
        'quant_vendas': quant_vendas,
        'desconto_geral': desconto_geral,
        'acrescimo_geral': acrescimo_geral,
        'periodo': periodo,
        'id_titulo': id_titulo,
        'nome_usuario': nome_usuario,
    }
    return render(request, 'contas_a_receber.html', context)

@login_required(login_url='/')
def quant_parcela(request):
    if request.method == "POST":
        dados = request.POST.dict()
        caixa = dados.get("caixa")
        parcelas = str(dados.get('parcelas'))
        quant_parcelas_cadastradas = len(Venda.objects.filter(caixa=caixa))
        if quant_parcelas_cadastradas == 1:
            if parcelas and caixa:
                caixa = dados.get("idcaixa")
                venda = Venda.objects.get(id=caixa)
                total = dados.get("total") if dados.get("total") != "" else venda.total
                if venda and venda.parcelas.strip() == "1 / 1" or "None":
                    venda.parcelas = "1 / " + parcelas
                    venda.total = total
                    venda.save()
    return contas_receber(request)

@login_required(login_url='/')
def nova_parcela(request):
    if request.method == "POST":
        nome_usuario = request.user.username
        dados = request.POST.dict()
        acao = dados.get('action')
        if acao == "nova_parcela":
            caixa = dados.get("caixa")
            venda = Venda.objects.filter(caixa=caixa).first()
            parcela = venda.parcelas
            if parcela != "1 / 1":
                parcela = int(parcela[4:])
                quant_parcelas_cadastradas = len(Venda.objects.filter(caixa=caixa))+1
                if not quant_parcelas_cadastradas > parcela:
                    cliente = venda.cliente
                    forma_pg = venda.forma_pg
                    frete = venda.frete
                    data_finalizacao = venda.data_finalizacao
                    vencimento = dados.get("vencimento")
                    if not vencimento:
                        vencimento = None
                    total = dados.get("total")
                    total = Decimal(total.replace(',', '.'))
                    obs = dados.get("obs")
                    parcela = str(quant_parcelas_cadastradas) + " / " + str(parcela)
                    nova_parcela = Venda.objects.create(caixa=caixa, frete=frete, usuario=nome_usuario, cliente=cliente, data_finalizacao=data_finalizacao,
                                    forma_pg=forma_pg, parcelas=parcela, vencimento=vencimento, total=total, obs=obs)
        elif acao == "alterar":
            caixa = dados.get("idcaixa")
            novo_vencimento = dados.get('vencimento')
            novo_pagamento = dados.get('data_pg')
            novo_desconto = Decimal(dados.get('desconto'))
            novo_acrescimo = dados.get('acrescimo')
            novo_total = dados.get('total')
            novo_obs = dados.get('obs')
            venda = Venda.objects.get(id=caixa)
            if novo_vencimento:
                venda.vencimento = datetime.strptime(novo_vencimento, '%Y-%m-%d').date()
            if novo_pagamento:
                venda.data_pg = datetime.strptime(novo_pagamento, '%Y-%m-%d').date()
            venda.desconto = Decimal(novo_desconto) if novo_desconto else Decimal('0.00')
            venda.acrescimo = Decimal(novo_acrescimo) if novo_acrescimo else Decimal('0.00')
            venda.total = Decimal(novo_total) if novo_total else Decimal('0.00')
            venda.obs = novo_obs if novo_obs else ""
            venda.save()
    return contas_receber(request)


################ RELATORIO CONTAS A PAGAR
@login_required(login_url='/')
def contas_pagar(request, id_titulo=None, data_inicial=None, data_final=None, filtro='todos', ordenar_por='caixa'):
    relatorio = []
    dados_caixa = {}
    periodo = {}
    if request.method == "POST":
        filtro = request.POST.get('titulos_pg')
        ordenar_por = request.POST.get('ordenar_por', 'caixa')
        id_titulo = request.POST.get('id_titulo')
        data_inicial = request.POST.get('data_inicial')
        data_final = request.POST.get('data_final')
        try:
            if data_inicial:
                data_inicial = datetime.strptime(data_inicial, '%d/%m/%Y').strftime('%Y-%m-%d')
            if data_final:
                data_final = datetime.strptime(data_final, '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            raise ValidationError('Formato de data inválido. Use o formato dd/mm/yyyy.')
    compras = Compra.objects.all()
    if not data_inicial:
        data_inicial = now().date()
    if not data_final:
        data_final = now().date()
    if data_inicial and data_final:
        compras = compras.filter(data_finalizacao__date__range=[data_inicial, data_final])
    if filtro == "nao":
        compras = compras.filter(data_pg__isnull=True)
    elif filtro == "sim":
        compras = compras.filter(data_pg__isnull=False)
    compras = compras.order_by(ordenar_por)
    total_compras = compras.aggregate(total=Sum('total'))['total'] or 0
    quant_compras = compras.count()
    desconto_geral = compras.aggregate(desconto=Sum('desconto'))['desconto'] or 0
    acrescimo_geral = compras.aggregate(acrescimo=Sum('acrescimo'))['acrescimo'] or 0
    total_compras = total_compras + acrescimo_geral - desconto_geral
    for item in compras:
        if not any(d['caixa'] == item.caixa and d['parcela'] == item.parcelas for d in relatorio):
            novo_relatorio = {
                'id': item.id,
                'nf': item.nf if item.nf else "",
                'caixa': item.caixa if item.caixa else "",
                'fornecedor': item.fornecedor.nome if item.fornecedor else "",
                'data_venda': item.data_finalizacao if item.data_finalizacao else "",
                'data_chegada': item.data_chegada if item.data_chegada else "",
                'forma_pg': item.forma_pg.nome if item.forma_pg else "",
                'frete': item.frete if item.frete else "",
                'parcela': item.parcelas if item.parcelas else "",
                'vencimento': item.vencimento if item.vencimento else "",
                'pagamento': item.data_pg if item.data_pg else "",
                'desconto': item.desconto if item.desconto else Decimal('0.00'),
                'acrescimo': item.acrescimo if item.acrescimo else Decimal('0.00'),
                'total_pg': (item.total + item.acrescimo - item.desconto) if item.total else Decimal('0.00'),
                'obs': item.obs if item.obs else "",
            }

            relatorio.append(novo_relatorio)

    if id_titulo:
        compra = compras.filter(id=id_titulo).first()
        if compra:
            dados_caixa = {
                'fornecedor': compra.fornecedor.nome if compra.fornecedor else "",
                'nf': compra.nf if compra.nf else "",
                'id_caixa': id_titulo,
                'caixa': compra.caixa if compra.caixa else None,
                'data_pg': compra.data_pg if compra.data_pg else None,
                'valor': float(compra.total) if compra.total else 0.00,
                'acrescimo': float(compra.acrescimo) if compra.acrescimo else 0.00,
                'desconto': float(compra.desconto) if compra.desconto else 0.00,
                'vencimento': compra.vencimento if compra.vencimento else None,
                'parcela': compra.parcelas if compra.parcelas else "",
                'forma_pg': compra.forma_pg.nome if compra.forma_pg else "",
                'obs': compra.obs if compra.obs else "",
            }
            dados_caixa['desconto'] = str(dados_caixa['desconto']).replace(',', '.')
            dados_caixa['acrescimo'] = str(dados_caixa['acrescimo']).replace(',','.')
            dados_caixa['valor'] = str(dados_caixa['valor']).replace(',','.')
    
    if request.method == "POST":
        if isinstance(data_inicial, str):
            data_inicial = data_inicial[8:10] + "/" + data_inicial[5:7] + "/" + data_inicial[:4]
        if isinstance(data_final, str):
            data_final = data_final[8:10] + "/" + data_final[5:7] + "/" + data_final[:4]
    else:
        if isinstance(data_final, date):
            data_final = data_final.strftime("%d/%m/%Y")
        if isinstance(data_inicial, date):
            data_inicial = data_inicial.strftime("%d/%m/%Y")
    periodo = {
        'data_inicial': data_inicial,
        'data_final': data_final,
    }
    nome_usuario = request.user.username
    context = {
        'relatorio': relatorio,
        'dados_caixa': dados_caixa,
        'filtro': filtro,
        'ordenar_por': ordenar_por,
        'total_compras': total_compras,
        'quant_compras': quant_compras,
        'desconto_geral': desconto_geral,
        'acrescimo_geral': acrescimo_geral,
        'periodo': periodo,
        'id_titulo': id_titulo,
        'nome_usuario': nome_usuario,
    }
    return render(request, "contas_a_pagar.html", context)

@login_required(login_url='/')
def quant_parcela_pagar(request):
    if request.method == "POST":
        dados = request.POST.dict()
        caixa = dados.get("caixa")
        parcelas = str(dados.get('parcelas'))
        quant_parcelas_cadastradas = len(Compra.objects.filter(caixa=caixa))
        if quant_parcelas_cadastradas == 1:
            if parcelas and caixa:
                caixa = dados.get("idcaixa")
                venda = Compra.objects.get(id=caixa)
                total = dados.get("total") if dados.get("total") != "" else venda.total
                if venda and venda.parcelas.strip() == "1 / 1" or "None":
                    venda.parcelas = "1 / " + parcelas
                    venda.total = total
                    venda.save()
    return contas_pagar(request)

@login_required(login_url='/')
def nova_parcela_pagar(request):
    if request.method == "POST":
        nome_usuario = request.user.username
        dados = request.POST.dict()
        acao = dados.get('action')
        if acao == "nova_parcela":
            caixa = dados.get("caixa")
            compra = Compra.objects.filter(caixa=caixa).first()
            parcela = compra.parcelas
            if parcela != "1 / 1":
                parcela = int(parcela[4:])
                quant_parcelas_cadastradas = len(Compra.objects.filter(caixa=caixa))+1
                if not quant_parcelas_cadastradas > parcela:
                    cliente = compra.fornecedor
                    forma_pg = compra.forma_pg
                    data_finalizacao = compra.data_finalizacao
                    frete = compra.frete
                    nf = compra.nf
                    data_chegada = compra.data_chegada
                    vencimento = dados.get("vencimento")
                    if not vencimento:
                        vencimento = None
                    total = dados.get("total")
                    total = Decimal(total.replace(',', '.'))
                    obs = dados.get("obs")
                    parcela = str(quant_parcelas_cadastradas) + " / " + str(parcela)
                    nova_parcela = Compra.objects.create(caixa=caixa, data_chegada=data_chegada, nf=nf, usuario=nome_usuario, frete=frete, fornecedor=cliente, data_finalizacao=data_finalizacao,
                                    forma_pg=forma_pg, parcelas=parcela, vencimento=vencimento, total=total, obs=obs)
        elif acao == "alterar":
            caixa = dados.get("idcaixa")
            novo_vencimento = dados.get('vencimento')
            novo_pagamento = dados.get('data_pg')
            novo_desconto = Decimal(dados.get('desconto'))
            novo_acrescimo = dados.get('acrescimo')
            novo_total = dados.get('total')
            novo_obs = dados.get('obs')
            venda = Compra.objects.get(id=caixa)
            if novo_vencimento:
                venda.vencimento = datetime.strptime(novo_vencimento, '%Y-%m-%d').date()
            if novo_pagamento:
                venda.data_pg = datetime.strptime(novo_pagamento, '%Y-%m-%d').date()
            venda.desconto = Decimal(novo_desconto) if novo_desconto else Decimal('0.00')
            venda.acrescimo = Decimal(novo_acrescimo) if novo_acrescimo else Decimal('0.00')
            venda.total = Decimal(novo_total) if novo_total else Decimal('0.00')
            venda.obs = novo_obs if novo_obs else ""
            venda.save()
    return contas_pagar(request)


################ CAIXA COMPRAS
@login_required(login_url='/')
def caixa_view_compra(request, n_caixa=None, lista_caixa=None, select_produto=None):
    produtos = Produtos_1.objects.order_by('nome')
    forma_pg = Forma_PG.objects.order_by('nome')
    fornecedores = Fornecedor.objects.order_by('nome')
    caixa = Caixa_compra.objects.all()
    subtotal = 0
    if n_caixa:
        n_caixa = n_caixa
    else:   
        max_id = caixa.aggregate(Max('caixa_aberto'))['caixa_aberto__max']
        n_caixa = (max_id or 0) + 1
    if lista_caixa:
        for item in lista_caixa:
            subtotal += item.total
    nome_usuario = request.user.username

    context = {"produtos": produtos, "n_caixa": n_caixa, "lista_caixa": lista_caixa, "subtotal": subtotal,
               "forma_pg": forma_pg, "fornecedores": fornecedores, "nome_usuario": nome_usuario, 'select_produto': select_produto}
    return render(request, 'caixa_compra.html', context)

@login_required(login_url='/')
def adicionar_carrinho_compra(request):
    if request.method == "POST":
        dados = request.POST.dict()
        n_caixa = dados.get('n_caixa')
        cod_produto = dados.get('cod_produto')
        if cod_produto:
            lista_caixa = Caixa_compra.objects.filter(caixa_aberto=n_caixa) 
            select_produto = Produtos_1.objects.get(cod_produto=cod_produto) if Produtos_1.objects.filter(cod_produto=cod_produto) else None
            return caixa_view_compra(request, n_caixa, lista_caixa, select_produto)
        produto_id = dados.get('produto')
        quantidade = dados.get('quantidade')
        valor_uni = dados.get('valor_uni')
        if produto_id and quantidade and valor_uni:
            quantidade = Decimal(quantidade)
            valor_uni = Decimal(valor_uni)
            produto = Produtos_1.objects.get(id=produto_id)
            caixa, criado = Caixa_compra.objects.get_or_create(caixa_aberto=n_caixa, produto=produto, 
                                                        quantidade=quantidade, valor_uni=valor_uni, finalizado=False)
            caixa.total = (caixa.quantidade * caixa.valor_uni)
            caixa.save()
    lista_caixa = Caixa_compra.objects.filter(caixa_aberto=n_caixa) 
    return caixa_view_compra(request, n_caixa, lista_caixa)

@login_required(login_url='/')
def remover_carrinho_compra(request):
    if request.method == "POST":
        dados = request.POST.dict()
        n_item = int(dados.get('n_item'))
        n_caixa = dados.get('n_caixa')
        lista_caixa = list(Caixa_compra.objects.filter(caixa_aberto=n_caixa))
        if lista_caixa:
            n_item_excluir = n_item-1
            lista_caixa[n_item_excluir].delete()
            lista_caixa = list(Caixa_compra.objects.filter(caixa_aberto=n_caixa))
    return caixa_view_compra(request, n_caixa, lista_caixa)

@login_required(login_url='/')
def finalizar_compra(request):
    if request.method=="POST":
        nome_usuario = request.user.username
        dados = request.POST.dict()
        acao = dados.get('action')
        if acao == "excluir_item":
            n_item = int(dados.get('n_item'))
            n_caixa = dados.get('n_caixa')
            lista_caixa = list(Caixa_compra.objects.filter(caixa_aberto=n_caixa))
            if lista_caixa:
                n_item_excluir = n_item-1
                lista_caixa[n_item_excluir].delete()
                lista_caixa = list(Caixa_compra.objects.filter(caixa_aberto=n_caixa))
            return caixa_view_compra(request, n_caixa, lista_caixa)
        elif acao == "finalizar_compra":
            n_caixa = dados.get('n_caixa')	
            nf = dados.get('nf')
            data_compra = dados.get('data_compra')	
            data_chegada = dados.get('data_chegada')	
            frete = dados.get('frete')	
            forma_pg_id = dados.get('forma_pg')
            obs = dados.get('obs')
            cliente_id = dados.get('cliente')
            total = dados.get('subtotal')
            total = Decimal(total.replace(',', '.'))
            fornecedor = get_object_or_404(Fornecedor, id=cliente_id) if cliente_id else Fornecedor.objects.get(id=1)
            forma_pg = get_object_or_404(Forma_PG, id=forma_pg_id) if forma_pg_id else Forma_PG.objects.get(id=1)

            if n_caixa and forma_pg and fornecedor:
                if forma_pg.id not in [4, 5, 6]:
                    vencimento = timezone.now()
                    data_pg = timezone.now()
                else: 
                    vencimento = None
                    data_pg = None
                parcela = "1 / 1"
                caixa = Caixa_compra.objects.filter(caixa_aberto=n_caixa)
                for item in caixa:
                    item.finalizado = True
                    item.save()
                    produto = item.produto.nome
                    quantidade = item.quantidade
                    estoque = Produtos_1.objects.get(nome=produto)
                    estoque.estoque += quantidade
                    estoque.save()
                venda, criar = Compra.objects.get_or_create(caixa=n_caixa, usuario=nome_usuario, nf=nf, data_finalizacao = timezone.now(), data_compra=data_compra,  
                                                        data_chegada=data_chegada, frete=frete,
                                                        forma_pg=forma_pg, obs=obs, fornecedor=fornecedor, total=total,
                                                        vencimento=vencimento, data_pg=data_pg, parcelas=parcela)
    return caixa_view_compra(request)

##########






