from django.shortcuts import render, redirect
from django.urls import reverse
from .models import *
from django.db.models import Max, Sum, Count
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from datetime import datetime, date, timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
import matplotlib.pyplot as plt
import io
import base64, urllib
import pandas as pd
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
import textwrap

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import win32print
import win32api
import os as o_s


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
    return render(request, 'menu.html', context)

@login_required(login_url='/')
def servicos(request, cod_servico=None, cod_produto=None):
    cod_produto = request.POST.get('cod_produto')
    id_produto = request.POST.get('id_produto')
    quantidade = request.POST.get('quantidade')
    desconto = request.POST.get('desconto')

    dados = request.POST.dict()
    nome_usuario = request.user.username
    veiculos = Veiculos.objects.order_by('placa') or ''
    cliente = Cliente.objects.order_by('nome') or ''
    servicos = TipoServicos.objects.order_by('nome') or ''
    if request.method == "POST":
        n_servico = dados.get('n_servico')
    else:
        max_os = OS.objects.aggregate(Max('os'))['os__max']
        n_servico = (max_os or 0) + 1

    profissionais = Profissional.objects.order_by('nome') or ''
    produtos = Produtos.objects.order_by('nome') or ''
    ex_servico = ""
    cod_produto2 = ""
    total_caixa = 0
    quant_parcelas = 1
    total_caixa_produto = 0
    caixa_servico = OS.objects.filter(os=n_servico)
    caixa_produto = OS_Produto.objects.filter(os=n_servico)
    quant_parcelas2 = [1]
    autofocus_s2 = False
    auto_focus_parcela = False
    if request.method == "POST":
        cod_servico = request.POST.get('cod_servico') or ""
        cod_produto = request.POST.get('cod_produto') or ""
        action = request.POST.get('acao') or request.POST.get('quant_parcelas')
        if action == "Lançar Serviço":
            os = dados.get('n_servico')
            servico_id = dados.get('servico')
            if not servico_id:
                return HttpResponse('<script>alert("Serviço não informado"); history.back();</script>')
            servico = TipoServicos.objects.filter(id=servico_id).first()
            if not servico:
                return HttpResponse('<script>alert("Serviço não encontrado"); history.back();</script>')

            acrescimo = Decimal(dados.get('acrescimo', 0).replace(',','.'))
            desconto = Decimal(dados.get('desconto', 0).replace(',','.'))
            veiculo = Veiculos.objects.get(id=1)
            profissional_id = dados.get('profissional')
            if not profissional_id:
                return HttpResponse('<script>alert("Profissional não informado"); history.back();</script>')

            profissional = Profissional.objects.filter(id=profissional_id).first()
            if not profissional:
                return HttpResponse('<script>alert("Profissional não cadastrado"); history.back();</script>')

            valor_servico = servicos.get(id=servico.id)
            total = Decimal(valor_servico.valor) + acrescimo - desconto
            servico = OS.   objects.create(os=os, servico=servico, valor_no_momento=valor_servico.valor, acrescimo=acrescimo, desconto=desconto, veiculo=veiculo, 
                                        profissional=profissional,
                                        total=total
                                        )
                                
            cod_servico = ""
            autofocus_s2 = True
            n_servico = os
        elif action == "Excluir Serviço":
            ex_servico = int(dados.get('excluir_servico'))
            if not ex_servico:
                return HttpResponse('<script>alert("Nº do serviço não informado para exclusão"); history.back();</script>')
            ex_servico = ex_servico - 1
            if ex_servico > -1 and ex_servico < len(caixa_servico):
                item_excluir = caixa_servico[ex_servico]
                item_excluir.delete()
                caixa_servico = OS.objects.filter(os=n_servico)
            autofocus_s2 = True
        elif action == "Lançar Produto":
            os = dados.get('n_servico')
            id_produto = dados.get('id_produto')
            if id_produto and id_produto.isdigit():  # Verifica se o ID está presente e é numérico
                if Produtos.objects.filter(id=id_produto).exists():
                    produto = Produtos.objects.get(id=id_produto)
                else:
                    return HttpResponse('<script>alert("Produto não encontrado"); history.back();</script>')
            else:
                return HttpResponse('<script>alert("Produto não informado ou ID inválido"); history.back();</script>')

            quantidade = Decimal(dados.get('quantidade').replace(',','.'))
            desconto = Decimal(dados.get('desconto').replace(',','.'))
            total = (produto.preco_venda * quantidade) - desconto
            produto.estoque -= quantidade
            produto.save()
            venda_produto = OS_Produto.objects.create(os=os, produto=produto, valor_no_momento=produto.preco_venda, quantidade=quantidade, desconto=desconto, total=total)
            cod_produto = ""
            n_servico = os
        elif action == "Excluir Produto":
            ex_produto = int(dados.get('excluir_produto'))
            ex_produto = ex_produto - 1
            if ex_produto > -1 and ex_produto < len(caixa_produto):
                item_excluir = caixa_produto[ex_produto]
                item_excluir.delete()
                caixa_produto = OS_Produto.objects.filter(os=n_servico)
            cod_produto = ""
            n_servico = dados.get('n_servico')
        elif action == "Fechar Serviço / Venda":
            saldo = Decimal(0)
            quant_parcelas = int(dados.get('quant_parcelas', 0))
            tg = Decimal(dados.get('tg').replace('R$', '').replace(',', '.').strip())
            os = dados.get('n_servico')
            forma_pg = dados.get('forma_pg')
            pagador = Cliente.objects.get(id=dados.get('pagador')) if dados.get('pagador') else None            
            veiculo = dados.get('veiculo')

            for i in range(1, quant_parcelas + 1):
                valor = Decimal(dados.get(f'valor_{i}', '').replace(',','.'))
                saldo += valor 
            if tg != saldo:
                return HttpResponse('<script>alert("Total das parcelas é diferente do Total Geral"); history.back();</script>')
                
            for i in range(1, quant_parcelas + 1):
                parcela = dados.get(f'parcela_{i}', '')
                vencimento = dados.get(f'vencimento_{i}', '')
                obs = dados.get(f'obs_{i}', '')

                lancar = Contas_receber.objects.create(os=os, parcela=parcela, forma_pg=forma_pg, pagador=pagador,
                                                        valor=valor,vencimento=vencimento, obs=obs)
            
            ts = float(dados.get('ts').replace('R$', '').replace(',', '').strip())
            tp = float(dados.get('tp').replace('R$', '').replace(',', '').strip())
            
            if ts > 0:
                servicos = OS.objects.filter(os=os)
                for servico in servicos:
                    servico.status = True
                    servico.veiculo = Veiculos.objects.get(id=veiculo)
                    servico.save()
            elif ts < 1:
                servico = OS.objects.create(os=os, status=True, obs="Somente venda de produtos")
            if tp > 0:
                produtos = OS_Produto.objects.filter(os=os)
                for produto in produtos:
                    produto.status = True
                    produto.produto.estoque -= produto.quantidade
                    produto.save()
            
            veiculo = Veiculos.objects.get(id=veiculo)

            # Caminho para salvar o PDF temporário
            # Caminho dinâmico para a pasta static/imagens/os
            BASE_DIR = Path(__file__).resolve().parent.parent
            pdf_path = o_s.path.join(BASE_DIR, "static", "imagens", "os", f"os_{os}.pdf")

            # Criando o PDF
            c = canvas.Canvas(pdf_path, pagesize=A4)
            width, height = A4
            y = height - 50  # Ajuste da posição do título para centralização
            c.setFont("Helvetica-Bold", 16)  # Fonte negrito e maior para destaque

            # Centralizando o texto
            c.drawCentredString(width / 2, y, "ORDEM DE SERVIÇO")
            y -= 25
            c.setLineWidth(1)  # Define a espessura da linha
            c.line(40, y, width - 40, y)  # Linha horizontal de ponta a ponta com margem
            y -= 25

            c.setFont("Helvetica", 10)  # Menor ainda para o restante do texto
            c.drawString(40, y, "NOME DA OFICINA - (71) 9 0000-0000")
            y -= 15
            c.drawString(40, y, "Endereço: ... - BA")
            y -= 15
            c.drawString(40, y, "CNPJ 00.000.000/0000-00")

            y -= 25
            c.setLineWidth(1)  # Define a espessura da linha
            c.line(40, y, width - 40, y)  # Linha horizontal de ponta a ponta com margem
            y -= 25

            c.drawString(40, y, f"Número do Serviço: {os}                                                                    Data: {servico.data_cadastro.strftime('%d/%m/%Y %H:%M:%S')}")
            y -= 15
            c.drawString(40, y, f"Cliente: {pagador.nome if pagador else 'Não especificado'}")
            y -= 15
            c.drawString(40, y, f"CPF: {pagador.cpf_cnpj}                                                                        Telefone: {pagador.telefone if pagador.telefone else ''} / {pagador.whatsapp if pagador.whatsapp else ''}")
            y -= 15
            c.drawString(40, y, f"Veículo: {veiculo.marca.nome} {veiculo.marca.modelo} {veiculo.ano}                                  Placa: {veiculo.placa}")
            
            y -= 25
            c.setLineWidth(1)  # Define a espessura da linha
            c.line(40, y, width - 40, y)  # Linha horizontal de ponta a ponta com margem
            y -= 25

            # Tabela dos produtos vendidos
            if tp > 0:
                y = height - 280  # Posição inicial dos produtos
                c.setFont("Helvetica-Bold", 13)
                c.drawString(70, y, "Produtos Vendidos")
                y -= 25
                c.setFont("Helvetica-Bold", 10)
 
                # Definir colunas
                coluna_cod_produto = 40
                coluna_nome_produto = 75
                coluna_quantidade = 285
                coluna_valor_unitario = 370
                coluna_desconto = 425
                coluna_total = 470

                # Cabeçalho
                c.drawString(coluna_cod_produto, y, "Cod")
                c.drawString(coluna_nome_produto, y, "Produto")
                c.drawRightString(coluna_quantidade + 50, y, "Quantidade")
                c.drawRightString(coluna_valor_unitario + 50, y, "Valor Unitário")
                c.drawRightString(coluna_desconto + 50, y, "Desconto")
                c.drawRightString(coluna_total + 50, y, "Total")
                y -= 15  # Espaço para os dados
                c.setFont("Helvetica", 10)

                total_itens = 0
                total_quantidade = 0
                total_desconto = 0
                total_geral = 0

                # Listagem de produtos
                for produto in produtos:

                    if y < 100:  # Se y for menor que 100, cria uma nova página
                        c.showPage()
                        y = height - 50  # Reinicia y na nova página
                        c.setFont("Helvetica-Bold", 13)
                        c.drawString(70, y, "Produtos Vendidos (Continuação OS {os})")
                        y -= 25
                        c.setFont("Helvetica", 10)

                    y -= 8
                    c.drawString(coluna_cod_produto, y, f"{produto.produto.cod_produto:<10}")
                    c.drawString(coluna_nome_produto, y, f"{produto.produto.nome:<45}")
                    c.drawRightString(coluna_quantidade + 50, y, f"{produto.quantidade:>8.3f}")
                    c.drawRightString(coluna_valor_unitario + 50, y, f"{produto.produto.preco_venda:>18.2f}")
                    c.drawRightString(coluna_desconto + 50, y, f"{produto.desconto:>18.2f}")
                    c.drawRightString(coluna_total + 50, y, f"{produto.total:>18.2f}")

                    total_itens += 1
                    total_quantidade += produto.quantidade
                    total_desconto += produto.desconto
                    total_geral += produto.total

                    y -= 4  # Espaçamento entre linhas
                    c.setLineWidth(0.5)
                    c.line(40, y, width - 40, y)
                    y -= 4

                c.setFont("Helvetica-Bold", 10)

                y -= 9
                # Exibe os totais abaixo da tabela
                c.drawString(coluna_cod_produto, y, f"Total:")
                c.drawString(coluna_nome_produto, y, f"{total_itens}")
                c.drawRightString(coluna_quantidade + 50, y, f"{total_quantidade:>8.3f}")
                c.drawRightString(coluna_desconto + 50, y, f"{total_desconto:>18.2f}")
                c.drawRightString(coluna_total + 50, y, f"{total_geral:>18.2f}")
                y -= 50  # Espaço extra após a tabela de produtos
            
            # Tabela dos serviços realizados
            if ts > 0:
                if y < 150:  # Se não há espaço suficiente, cria uma nova página
                    c.showPage()
                    y = height - 50  # Reinicia y na nova página

                c.setFont("Helvetica-Bold", 14)
                c.drawString(70, y, "Serviços Realizados")
                y -= 25
                c.setFont("Helvetica-Bold", 10)

                # Definir colunas dos serviços
                coluna_id = 40
                coluna_servico = 75
                coluna_total = 300
                coluna_profissional = 430

                c.drawString(coluna_id, y, "Cod")
                c.drawString(coluna_servico, y, "Serviço")
                c.drawRightString(coluna_total + 50, y, "Total")
                c.drawRightString(coluna_profissional + 50, y, "Profissional")

                y -= 15
                c.setFont("Helvetica", 10)

                total_itens = 0
                total_servico = 0
                # Listagem de serviços
                for servico in servicos:
                    if y < 100:  # Se não há mais espaço, nova página
                        c.showPage()
                        y = height - 50
                        c.setFont("Helvetica-Bold", 13)
                        c.drawString(70, y, "Serviços Realizados (Continuação OS {os})")
                        y -= 25
                        c.setFont("Helvetica", 10)

                    y -= 8
                    c.drawString(coluna_id, y, f"{servico.servico.id:<45}")
                    c.drawString(coluna_servico, y, f"{servico.servico.nome:<45}")
                    c.drawRightString(coluna_total + 50, y, f"{servico.total:>15.2f}")
                    c.drawRightString(coluna_profissional + 50, y, f"{servico.profissional.nome:>25}")

                    y -= 4
                    c.line(40, y, width - 40, y)
                    y -= 4
                    total_itens += 1
                    total_servico += servico.total
                
                y -= 9
                c.setFont("Helvetica-Bold", 10)
                c.drawString(coluna_id, y, "Total:")
                c.drawString(coluna_servico, y, f"{total_itens}")
                c.drawRightString(coluna_total + 50, y, f"{total_servico}")
                y -= 50
            
            # Parcelas para pagamento
            c.setFont("Helvetica-Bold", 13)
            c.drawString(70, y, "Parcelas da Venda / Serviços")
            y -= 25

            c_parcela = 45
            c_forma_pg = 90
            c_valor = 195
            c_vencimento = 255
            
            c.setFont("Helvetica-Bold", 10)
            c.drawString(c_parcela, y, "Parcela")
            c.drawString(c_forma_pg, y, "Forma de Pagamento")
            c.drawRightString(c_valor + 50, y, "Valor")
            c.drawRightString(c_vencimento + 50, y, "Vencimento")
            c.setFont("Helvetica", 10)
            y -= 10 
            observacoes = []
            for i in range(1, quant_parcelas + 1):
                if y < 100:  # Se não há mais espaço, nova página
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica-Bold", 13)
                    c.drawString(70, y, f"Parcelas da Venda / Serviços (Continuação OS {os})")
                    y -= 25
                    c.setFont("Helvetica", 10)
                
                parcela = dados.get(f'parcela_{i}', '')
                forma_pg = dados.get('forma_pg', '')
                valor = Decimal(dados.get(f'valor_{i}', '').replace(',', '.'))
                vencimento = dados.get(f'vencimento_{i}', '')
                vencimento_formatado = datetime.strptime(vencimento, "%Y-%m-%d").strftime("%d/%m/%Y")
                obs = dados.get(f'obs_{i}', '')

                # Adiciona a observação numerada à lista
                if obs.strip():
                    observacoes.append(f"{len(observacoes) + 1}. {obs}")

                y -= 8

                c.drawString(c_parcela, y, f"{parcela:<45}")
                c.drawString(c_forma_pg, y, f"{forma_pg:<45}")
                c.drawRightString(c_valor + 50, y, f"{valor:>15.2f}")
                c.drawRightString(c_vencimento + 50, y, f"{vencimento_formatado:>25}")

                y -= 4
                c.line(40, y, width - 40, y)
                y -= 4
            
            # Observações
            y -= 50
            if observacoes:
                c.setFont("Helvetica-Bold", 14)
                c.drawString(70, y, "Observação")
                y -= 25
                c.setFont("Helvetica", 10)

                largura_maxima = 80  # Ajuste esse valor conforme necessário

                # Desenhar todas as observações armazenadas
                for obs in observacoes:
                    if y < 100:  # Se não há mais espaço, nova página
                        c.showPage()
                        y = height - 50
                        c.setFont("Helvetica-Bold", 13)
                        c.drawString(70, y, f"Observação (Continuação OS {os})")
                        y -= 25
                        c.setFont("Helvetica", 10)
                    
                    # Quebrar a observação em várias linhas conforme a largura máxima
                    linhas = textwrap.wrap(obs, width=largura_maxima)

                    for linha in linhas:
                        if y < 100:  # Se não há mais espaço, nova página
                            c.showPage()
                            y = height - 50
                            c.setFont("Helvetica-Bold", 13)
                            c.drawString(70, y, f"Observação (Continuação OS {os})")
                            y -= 25
                            c.setFont("Helvetica", 10)
                        
                        c.drawString(45, y, linha)
                        y -= 15  # Ajuste do espaçamento entre linhas
                y -= 50
            # Retirado por...
            altura_caixa = 60  # Altura das caixas de texto
            largura_recebido = 160  # Largura da caixa "RECEBIDO POR"
            largura_rg_cpf = 160  # Largura da caixa "RG / CPF"
            largura_data_hora = 160  # Largura da caixa "DATA / HORA"

            # Coordenadas X das caixas
            x_recebido = 80
            x_rg_cpf = 240
            x_data_hora = 400

            # Posição inicial do texto
            y -= 30  

            # Fonte e tamanho
            fonte = "Helvetica-Bold"
            tamanho_fonte = 10
            c.setFont(fonte, tamanho_fonte)

            # Função para centralizar o texto dentro da caixa
            def centralizar_texto(texto, x_centro, largura_caixa):
                largura_texto = c.stringWidth(texto, fonte, tamanho_fonte)
                return x_centro + (largura_caixa - largura_texto) / 2  # Calcula o X para centralizar

            # Desenhar os textos centralizados no topo das caixas
            c.drawString(centralizar_texto("RECEBIDO POR", x_recebido, largura_recebido), y, "RECEBIDO POR")
            c.drawString(centralizar_texto("RG / CPF", x_rg_cpf, largura_rg_cpf), y, "RG / CPF") 
            c.drawString(centralizar_texto("DATA / HORA", x_data_hora, largura_data_hora), y, "DATA / HORA")

            # Ajustar Y para que as bordas fiquem logo abaixo dos textos
            y -= 8  

            # Desenhar as bordas das caixas
            c.rect(x_recebido, y - altura_caixa + 5, largura_recebido, altura_caixa)  # Caixa "RECEBIDO POR"
            c.rect(x_rg_cpf, y - altura_caixa + 5, largura_rg_cpf, altura_caixa)  # Caixa "RG / CPF"
            c.rect(x_data_hora, y - altura_caixa + 5, largura_data_hora, altura_caixa)  # Caixa "DATA / HORA"

            # imagem_rodape = o_s.path.join(BASE_DIR, "static", "imagens", "logo_impressao.png")

            # # Posição da imagem (ajuste conforme necessário)
            # largura_imagem = 350  # Largura da imagem em pixels
            # altura_imagem = 40    # Altura da imagem em pixels
            # pos_x = width - largura_imagem - 10
            # pos_y = 20  # Define a posição no rodapé

            # # Adiciona a imagem ao PDF
            # c.drawImage(imagem_rodape, pos_x, pos_y, width=largura_imagem, height=altura_imagem, preserveAspectRatio=True, mask='auto')


            c.setFont("Helvetica-Bold", 15)  # Fonte maior para o título
            c.drawString(width - 180, 30, "CodeWave")  # Escrever o título no canto esquerdo
            c.setFont("Helvetica-Bold", 9)  # Fonte maior para o título

            # Definir fonte menor para os contatos
            c.setFont("Helvetica", 5)
            c.drawRightString(width - 62, 25, "71 9 1111-1111")  # Contato 1 à direita
            c.drawRightString(width - 62, 20, "71 9 1111-1112")  # Contato 2 abaixo
            c.drawRightString(width - 40, 15, "codewave.rb@gmail.com")  # Email abaixo



            # Salvar o PDF
            c.save()

            # print(f"DEBUG: pdf_path = {pdf_path}")

            # # Enviar para a impressora
            # printer_name = win32print.GetDefaultPrinter()
            # hprinter = win32print.OpenPrinter(printer_name)
            # printer_info = win32print.GetPrinter(hprinter, 2)
            # win32print.ClosePrinter(hprinter)

            pdf_abspath = o_s.path.abspath(pdf_path)

            n_servico = int(os) + 1
            context = {
                'veiculos':veiculos,
                'servicos':servicos,
                'cliente':cliente,
                'profissionais':profissionais,
                'n_servico':n_servico,
                'produtos':produtos,
            }

            

            return render(request, 'lancamento_servico.html', context)
        elif action:
            quant_parcelas = dados.get('quant_parcelas')
            if quant_parcelas is None:
                quant_parcelas = 1
            quant_parcelas2 = range(1, int(quant_parcelas) + 1)
            auto_focus_parcela = True
        
    for caixa in caixa_servico:
        total_caixa += caixa.total

    for caixa in caixa_produto:
        total_caixa_produto += caixa.total
        
    

    tg = total_caixa_produto + total_caixa or 0
    valor_parcela = Decimal(tg) / Decimal(quant_parcelas)
    valor_parcela = valor_parcela.quantize(Decimal('0.00'), rounding=ROUND_DOWN)
    saldo = (Decimal(valor_parcela) * Decimal(quant_parcelas)) - tg
    context = {'nome_usuario':nome_usuario,
                'veiculos':veiculos,
               'servicos':servicos,
               'cliente':cliente,
               'profissionais':profissionais,
               'n_servico':n_servico,
               'cod_servico':cod_servico if cod_servico else "",
               'caixa_servico':caixa_servico, 
               'total_caixa': total_caixa,
               'produtos':produtos,
               'cod_produto':cod_produto, 'cod_produto2': cod_produto2,
               'caixa_produto': caixa_produto,
               'total_caixa_produto':total_caixa_produto,
               'tg':tg, 'autofocus_s2':autofocus_s2,
               'quant_parcelas':quant_parcelas, 'quant_parcelas2':quant_parcelas2, 'valor_parcela':valor_parcela, 'saldo':saldo, 'auto_focus_parcela':auto_focus_parcela,
               }
    return render(request, 'lancamento_servico.html', context)

@login_required(login_url='/')
def servicossssssssss(request, cod_servico=None, cod_produto=None):
    cod_produto = request.POST.get('cod_produto')
    id_produto = request.POST.get('id_produto')
    quantidade = request.POST.get('quantidade')
    desconto = request.POST.get('desconto')

    dados = request.POST.dict()
    nome_usuario = request.user.username
    veiculos = Veiculos.objects.order_by('placa') or ''
    cliente = Cliente.objects.order_by('nome') or ''
    servicos = TipoServicos.objects.order_by('nome') or ''
    if request.method == "POST":
        n_servico = dados.get('n_servico')
    else:
        max_os = OS.objects.aggregate(Max('os'))['os__max']
        n_servico = (max_os or 0) + 1

    profissionais = Profissional.objects.order_by('nome') or ''
    produtos = Produtos.objects.order_by('nome') or ''
    ex_servico = ""
    cod_produto2 = ""
    total_caixa = 0
    quant_parcelas = 1
    total_caixa_produto = 0
    caixa_servico = OS.objects.filter(os=n_servico)
    caixa_produto = OS_Produto.objects.filter(os=n_servico)
    quant_parcelas2 = [1]
    autofocus_s2 = False
    auto_focus_parcela = False
    if request.method == "POST":
        cod_servico = request.POST.get('cod_servico') or ""
        cod_produto = request.POST.get('cod_produto') or ""
        action = request.POST.get('acao') or request.POST.get('quant_parcelas')
        if action == "Lançar Serviço":
            os = dados.get('n_servico')
            servico_id = dados.get('servico')
            if not servico_id:
                return HttpResponse('<script>alert("Serviço não informado"); history.back();</script>')
            servico = TipoServicos.objects.filter(id=servico_id).first()
            if not servico:
                return HttpResponse('<script>alert("Serviço não encontrado"); history.back();</script>')

            acrescimo = Decimal(dados.get('acrescimo', 0).replace(',','.'))
            desconto = Decimal(dados.get('desconto', 0).replace(',','.'))
            veiculo = Veiculos.objects.get(id=1)
            profissional_id = dados.get('profissional')
            if not profissional_id:
                return HttpResponse('<script>alert("Profissional não informado"); history.back();</script>')

            profissional = Profissional.objects.filter(id=profissional_id).first()
            if not profissional:
                return HttpResponse('<script>alert("Profissional não cadastrado"); history.back();</script>')

            valor_servico = servicos.get(id=servico.id)
            total = Decimal(valor_servico.valor) + acrescimo - desconto
            servico = OS.   objects.create(os=os, servico=servico, valor_no_momento=valor_servico.valor, acrescimo=acrescimo, desconto=desconto, veiculo=veiculo, 
                                        profissional=profissional,
                                        total=total
                                        )
                                
            cod_servico = ""
            autofocus_s2 = True
            n_servico = os
        elif action == "Excluir Serviço":
            ex_servico = int(dados.get('excluir_servico'))
            if not ex_servico:
                return HttpResponse('<script>alert("Nº do serviço não informado para exclusão"); history.back();</script>')
            ex_servico = ex_servico - 1
            if ex_servico > -1 and ex_servico < len(caixa_servico):
                item_excluir = caixa_servico[ex_servico]
                item_excluir.delete()
                caixa_servico = OS.objects.filter(os=n_servico)
            autofocus_s2 = True
        elif action == "Lançar Produto":
            os = dados.get('n_servico')
            id_produto = dados.get('id_produto')
            if id_produto and id_produto.isdigit():  # Verifica se o ID está presente e é numérico
                if Produtos.objects.filter(id=id_produto).exists():
                    produto = Produtos.objects.get(id=id_produto)
                else:
                    return HttpResponse('<script>alert("Produto não encontrado"); history.back();</script>')
            else:
                return HttpResponse('<script>alert("Produto não informado ou ID inválido"); history.back();</script>')

            quantidade = Decimal(dados.get('quantidade').replace(',','.'))
            desconto = Decimal(dados.get('desconto').replace(',','.'))
            total = (produto.preco_venda * quantidade) - desconto
            produto.estoque -= quantidade
            produto.save()
            venda_produto = OS_Produto.objects.create(os=os, produto=produto, valor_no_momento=produto.preco_venda, quantidade=quantidade, desconto=desconto, total=total)
            cod_produto = ""
            n_servico = os
        elif action == "Excluir Produto":
            ex_produto = int(dados.get('excluir_produto'))
            ex_produto = ex_produto - 1
            if ex_produto > -1 and ex_produto < len(caixa_produto):
                item_excluir = caixa_produto[ex_produto]
                item_excluir.delete()
                caixa_produto = OS_Produto.objects.filter(os=n_servico)
            cod_produto = ""
            n_servico = dados.get('n_servico')
        elif action == "Fechar Serviço / Venda":
            saldo = Decimal(0)
            quant_parcelas = int(dados.get('quant_parcelas', 0))
            tg = Decimal(dados.get('tg').replace('R$', '').replace(',', '.').strip())
            os = dados.get('n_servico')
            forma_pg = dados.get('forma_pg')
            pagador = Cliente.objects.get(id=dados.get('pagador')) if dados.get('pagador') else None            
            veiculo = dados.get('veiculo')

            for i in range(1, quant_parcelas + 1):
                valor = Decimal(dados.get(f'valor_{i}', '').replace(',','.'))
                saldo += valor 
            if tg != saldo:
                return HttpResponse('<script>alert("Total das parcelas é diferente do Total Geral"); history.back();</script>')
                
            for i in range(1, quant_parcelas + 1):
                parcela = dados.get(f'parcela_{i}', '')
                vencimento = dados.get(f'vencimento_{i}', '')
                obs = dados.get(f'obs_{i}', '')

                lancar = Contas_receber.objects.create(os=os, parcela=parcela, forma_pg=forma_pg, pagador=pagador,
                                                        valor=valor,vencimento=vencimento, obs=obs)
            
            ts = float(dados.get('ts').replace('R$', '').replace(',', '').strip())
            tp = float(dados.get('tp').replace('R$', '').replace(',', '').strip())
            
            if ts > 0:
                servicos = OS.objects.filter(os=os)
                for servico in servicos:
                    servico.status = True
                    servico.veiculo = Veiculos.objects.get(id=veiculo)
                    servico.save()
            elif ts < 1:
                servico = OS.objects.create(os=os, status=True, obs="Somente venda de produtos")
            if tp > 0:
                produtos = OS_Produto.objects.filter(os=os)
                for produto in produtos:
                    produto.status = True
                    produto.produto.estoque -= produto.quantidade
                    produto.save()
            
            veiculo = Veiculos.objects.get(id=veiculo)
                # Exemplo de como construir e exibir a "folha" no terminal
            print("\n\n-------------------------- ORDEM DE SERVIÇO --------------------------\n\n")
            print("NOME DA OFICINA - (71) 9 0000-0000")
            print("Endereço: ... - BA")
            print("CNPJ 00.000.000/0000-00\n\n\n")
            print(f"Número do Serviço: {os}         Data: {servico.data_cadastro.strftime('%d/%m/%Y %H:%M:%S')}")
            print(f"Cliente: {pagador.nome if pagador else 'Não especificado'}         CPF: {pagador.cpf_cnpj}         Telefone: {pagador.telefone if pagador.telefone else ''} / {pagador.whatsapp if pagador.whatsapp else ''}")
            print(f"Veículo: {veiculo.marca.nome} - {veiculo.marca.modelo} {veiculo.ano}         Placa: {veiculo.placa}" )
            print("\n-------------------------------------------------------------------------\n")

            if tp > 0:
                # Cabeçalho da tabela
                print('\n\n------------------------- Produtos Vendidos -------------------------')
                print(f"{'Cod':<6}{'Produto':<30}{'Qtd':>8}{'Valor Unitário':>18}{'Total':>15}")
                print('-' * 85)  # Linha separadora

                # Impressão das informações de cada produto
                for produto in produtos:
                    cod_produto = produto.produto.cod_produto  # Código do produto
                    nome_produto = produto.produto.nome       # Nome do produto
                    quantidade = produto.quantidade           # Quantidade vendida
                    valor_unitario = produto.produto.preco_venda  # Preço unitário do produto
                    total_produto = produto.total             # Total da venda (quantidade * preco_venda)

                    # Imprimir os dados na tabela com as colunas corretamente alinhadas
                    print(f"{cod_produto:<6}{nome_produto:<30}{quantidade:>8.3f}{valor_unitario:>18.2f}{total_produto:>15.2f}")
                
                print('-' * 85)  # Linha final

            print('\n\n------------------------ Parcelas da Venda ------------------------')
            print(f"{'Parcela':<10}{'Forma de PG':<20}{'Valor':>12}{'Vencimento':>15}")
            print('-' * 60)  # Linha separadora

            for i in range(1, quant_parcelas + 1):
                parcela = dados.get(f'parcela_{i}', '')
                forma_pg = dados.get('forma_pg', '')
                valor = Decimal(dados.get(f'valor_{i}', '').replace(',', '.'))
                vencimento = dados.get(f'vencimento_{i}', '')
                vencimento_formatado = datetime.strptime(vencimento, "%Y-%m-%d").strftime("%d/%m/%Y")
                print(f"{parcela:<10}{forma_pg:<20}{valor:>12.2f}{vencimento_formatado:>15}")

            print('-' * 60)  # Linha final

            n_servico = int(os) + 1
            context = {
                'veiculos':veiculos,
                'servicos':servicos,
                'cliente':cliente,
                'profissionais':profissionais,
                'n_servico':n_servico,
                'produtos':produtos,
            }

            

            return render(request, 'lancamento_servico.html', context)
        elif action:
            quant_parcelas = dados.get('quant_parcelas')
            if quant_parcelas is None:
                quant_parcelas = 1
            quant_parcelas2 = range(1, int(quant_parcelas) + 1)
            auto_focus_parcela = True
        
    for caixa in caixa_servico:
        total_caixa += caixa.total

    for caixa in caixa_produto:
        total_caixa_produto += caixa.total
        
    

    tg = total_caixa_produto + total_caixa or 0
    valor_parcela = Decimal(tg) / Decimal(quant_parcelas)
    valor_parcela = valor_parcela.quantize(Decimal('0.00'), rounding=ROUND_DOWN)
    saldo = (Decimal(valor_parcela) * Decimal(quant_parcelas)) - tg
    context = {'nome_usuario':nome_usuario,
                'veiculos':veiculos,
               'servicos':servicos,
               'cliente':cliente,
               'profissionais':profissionais,
               'n_servico':n_servico,
               'cod_servico':cod_servico if cod_servico else "",
               'caixa_servico':caixa_servico, 
               'total_caixa': total_caixa,
               'produtos':produtos,
               'cod_produto':cod_produto, 'cod_produto2': cod_produto2,
               'caixa_produto': caixa_produto,
               'total_caixa_produto':total_caixa_produto,
               'tg':tg, 'autofocus_s2':autofocus_s2,
               'quant_parcelas':quant_parcelas, 'quant_parcelas2':quant_parcelas2, 'valor_parcela':valor_parcela, 'saldo':saldo, 'auto_focus_parcela':auto_focus_parcela,
               }
    return render(request, 'lancamento_servico.html', context)

@login_required(login_url='/')
def caixa_view_compra(request, n_caixa=None, cod_produto=None):
    dados = request.POST.dict()
    nome_usuario = request.user.username
    quant_parcelas2 = [1]
    auto_focus_parcela = False
    produtos = Produtos.objects.order_by('nome')
    fornecedores = Fornecedor.objects.order_by('nome')
    total_caixa_produto = 0
    quant_parcelas = 1
    if request.method == "POST":
        n_caixa = dados.get('n_caixa')
    else:
        max_os = Caixa_compra.objects.aggregate(Max('os'))['os__max']
        n_caixa = (max_os or 0) + 1

    caixa_produto = Caixa_compra.objects.filter(os=n_caixa)
    

    if request.method == "POST":
        cod_produto = request.POST.get('cod_produto') or ""
        action = request.POST.get('acao') or request.POST.get('quant_parcelas')
        if action == "Lançar Produto":
            os = dados.get('n_caixa')
            id_produto = dados.get('id_produto')
            if id_produto and id_produto.isdigit():  # Verifica se o ID está presente e é numérico
                if Produtos.objects.filter(id=id_produto).exists():
                    produto = Produtos.objects.get(id=id_produto)
                else:
                    return HttpResponse('<script>alert("Produto não encontrado"); history.back();</script>')
            else:
                return HttpResponse('<script>alert("Produto não informado ou ID inválido"); history.back();</script>')

            quantidade = Decimal(dados.get('quantidade').replace(',','.'))
            valor_uni = Decimal(dados.get('valor_uni').replace(',','.'))
            total = quantidade * valor_uni
            produto.estoque += quantidade
            produto.save()
            venda_produto = Caixa_compra.objects.create(os=os, produto=produto, quantidade=quantidade, valor_uni=valor_uni, total=total)
            cod_produto = ""
            n_caixa = os
        elif action == "Excluir Produto":
            ex_produto = int(dados.get('excluir_produto'))
            ex_produto = ex_produto - 1
            if ex_produto > -1 and ex_produto < len(caixa_produto):
                item_excluir = caixa_produto[ex_produto]
                item_excluir.delete()
                caixa_produto = Caixa_compra.objects.filter(os=n_caixa)
            cod_produto = ""
            n_caixa = dados.get('n_caixa')
        elif action == "Fechar Compra":
            saldo = Decimal(0)
            quant_parcelas = int(dados.get('quant_parcelas', 0))
            tg = Decimal(dados.get('tg').replace('R$', '').replace(',', '.').strip())
            os = dados.get('n_caixa')
            forma_pg = dados.get('forma_pg')
            fornecedor = Fornecedor.objects.get(id=dados.get('fornecedor')) if dados.get('fornecedor') else None
            nf = dados.get('nf')
            data_compra = dados.get('data_compra')	
            data_chegada = dados.get('data_chegada')
            frete = dados.get('frete')

            for i in range(1, quant_parcelas + 1):
                valor = Decimal(dados.get(f'valor_{i}', '').replace(',','.'))
                saldo += valor 
            if tg != saldo:
                return HttpResponse('<script>alert("Total das parcelas é diferente do Total Geral"); history.back();</script>')
                
            for i in range(1, quant_parcelas + 1):
                parcela = dados.get(f'parcela_{i}', '')
                vencimento = dados.get(f'vencimento_{i}', '')
                obs = dados.get(f'obs_{i}', '')

                lancar = Contas_a_pagar.objects.create(os=os, nf=nf, data_compra=data_compra,data_chegada=data_chegada, frete=frete,  
                                                       parcela=parcela, forma_pg=forma_pg, fornecedor=fornecedor,
                                                        valor=valor,vencimento=vencimento, obs=obs, usuario=nome_usuario)
            
            caixa_c = Caixa_compra.objects.filter(os=os)
            for produto in caixa_c:
                produto.status = True
                produto.produto.estoque += produto.quantidade
                produto.save()

            n_caixa = int(os) + 1
            context = { 'n_caixa': n_caixa,
                        'produtos':produtos,
                        'nome_usuario': nome_usuario,
                        }
            return render(request, 'caixa_compra.html', context)
        elif action:
            quant_parcelas = dados.get('quant_parcelas')
            if quant_parcelas is None:
                quant_parcelas = 1
            quant_parcelas2 = range(1, int(quant_parcelas) + 1)
            auto_focus_parcela = True

    caixa_produto = Caixa_compra.objects.filter(os=n_caixa)

    for caixa in caixa_produto:
        total_caixa_produto += caixa.total
    
    tg = total_caixa_produto
    valor_parcela = Decimal(tg) / Decimal(quant_parcelas)
    valor_parcela = valor_parcela.quantize(Decimal('0.00'), rounding=ROUND_DOWN)
    saldo = (Decimal(valor_parcela) * Decimal(quant_parcelas)) - tg
    context = {'produtos': produtos,
               'n_caixa': n_caixa,'tg':tg,
               'fornecedores': fornecedores,'saldo':saldo,'valor_parcela':valor_parcela,
               'nome_usuario': nome_usuario,'auto_focus_parcela':auto_focus_parcela,
               'cod_produto':cod_produto, 'caixa_produto':caixa_produto, 'total_caixa_produto':total_caixa_produto, 'quant_parcelas':quant_parcelas,'quant_parcelas2':quant_parcelas2}
    return render(request, 'caixa_compra.html', context)


@login_required(login_url='/')
def contas_receber(request, id_titulo=None, data_inicial=None, data_final=None, filtro='todos', ordenar_por='os'):#
    relatorio = []
    dados_caixa = {}
    periodo = {}
    if request.method == "POST":
        if request.POST.get('action') == "Alterar Dados":
            dados = request.POST.dict()
            caixa = dados.get("idcaixa")
            novo_vencimento = dados.get('vencimento')
            novo_pagamento = dados.get('data_pg')
            novo_desconto = Decimal(dados.get('desconto'))
            novo_acrescimo = dados.get('acrescimo')
            novo_total = dados.get('total')
            novo_obs = dados.get('obs')
            
            venda = Contas_receber.objects.get(id=caixa)
            if novo_vencimento:
                venda.vencimento = datetime.strptime(novo_vencimento, '%Y-%m-%d').date()
            if novo_pagamento:
                venda.data_pg = datetime.strptime(novo_pagamento, '%Y-%m-%d').date()
            venda.desconto = Decimal(novo_desconto) if novo_desconto else Decimal('0.00')
            venda.acrescimo = Decimal(novo_acrescimo) if novo_acrescimo else Decimal('0.00')
            venda.valor = Decimal(novo_total) if novo_total else Decimal('0.00')
            venda.obs = novo_obs if novo_obs else ""
            venda.save()
        filtro = request.POST.get('titulos_pg')
        ordenar_por = request.POST.get('ordenar_por', 'os')
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
    vendas = Contas_receber.objects.all()
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
    total_vendas = vendas.aggregate(valor=Sum('valor'))['valor'] or 0
    quant_vendas = vendas.count()
    desconto_geral = vendas.aggregate(desconto=Sum('desconto'))['desconto'] or 0
    acrescimo_geral = vendas.aggregate(acrescimo=Sum('acrescimo'))['acrescimo'] or 0
    total_vendas = total_vendas + acrescimo_geral - desconto_geral

    for item in vendas:
        if not any(d['os'] == item.os and d['parcela'] == item.parcela for d in relatorio):
            novo_relatorio = {
                'id': item.id,
                'os': item.os if item.os else "",
                'cliente': item.pagador.nome if item.pagador else "",
                'data_venda': item.data_finalizacao if item.data_finalizacao else "",
                'forma_pg': item.forma_pg if item.forma_pg else "",
                'parcela': item.parcela if item.parcela else "",
                'vencimento': item.vencimento if item.vencimento else "",
                'pagamento': item.data_pg if item.data_pg else "",
                'desconto': item.desconto if item.desconto else Decimal('0.00'),
                'acrescimo': item.acrescimo if item.acrescimo else Decimal('0.00'),
                'total_pg': (item.valor + item.acrescimo - item.desconto) if item.valor else Decimal('0.00'),
                'obs': item.obs if item.obs else "",
            }
            relatorio.append(novo_relatorio)
    if id_titulo:
        venda = vendas.filter(id=id_titulo).first()
        if venda:
            dados_caixa = {
                'cliente': venda.pagador.nome if venda.pagador else "",
                'os': venda.os if venda.os else "",
                'id_caixa': id_titulo,
                'data_pg': venda.data_pg if venda.data_pg else None,
                'valor': float(venda.valor) if venda.valor else 0.00,
                'acrescimo': float(venda.acrescimo) if venda.acrescimo else 0.00,
                'desconto': float(venda.desconto) if venda.desconto else 0.00,
                'vencimento': venda.vencimento if venda.vencimento else None,
                'parcela': venda.parcela if venda.parcela else "",
                'forma_pg': venda.forma_pg if venda.forma_pg else "",
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
def contas_pagar(request, id_titulo=None, data_inicial=None, data_final=None, filtro='todos', ordenar_por='os'):
    relatorio = []
    dados_caixa = {}
    periodo = {}
    if request.method == "POST":
        if request.POST.get('action') == "Alterar Dados":
            dados = request.POST.dict()
            caixa = dados.get("idcaixa")
            novo_vencimento = dados.get('vencimento')
            novo_pagamento = dados.get('data_pg')
            novo_desconto = Decimal(dados.get('desconto'))
            novo_acrescimo = dados.get('acrescimo')
            novo_total = dados.get('total')
            novo_obs = dados.get('obs')
            
            venda = Contas_a_pagar.objects.get(id=caixa)
            if novo_vencimento:
                venda.vencimento = datetime.strptime(novo_vencimento, '%Y-%m-%d').date()
            if novo_pagamento:
                venda.data_pg = datetime.strptime(novo_pagamento, '%Y-%m-%d').date()
            venda.desconto = Decimal(novo_desconto) if novo_desconto else Decimal('0.00')
            venda.acrescimo = Decimal(novo_acrescimo) if novo_acrescimo else Decimal('0.00')
            venda.valor = Decimal(novo_total) if novo_total else Decimal('0.00')
            venda.obs = novo_obs if novo_obs else ""
            venda.save()

        filtro = request.POST.get('titulos_pg')
        ordenar_por = request.POST.get('ordenar_por', 'os')
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
        
    compras = Contas_a_pagar.objects.all()
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
    total_compras = compras.aggregate(valor=Sum('valor'))['valor'] or 0
    quant_compras = compras.count()
    desconto_geral = compras.aggregate(desconto=Sum('desconto'))['desconto'] or 0
    acrescimo_geral = compras.aggregate(acrescimo=Sum('acrescimo'))['acrescimo'] or 0
    total_compras = total_compras + acrescimo_geral - desconto_geral
    for item in compras:
        if not any(d['os'] == item.os and d['parcela'] == item.parcela for d in relatorio):
            novo_relatorio = {
                'id': item.id,
                'nf': item.nf if item.nf else "",
                'os': item.os if item.os else "",
                'fornecedor': item.fornecedor.nome if item.fornecedor else "",
                'data_venda': item.data_finalizacao if item.data_finalizacao else "",
                'data_chegada': item.data_chegada if item.data_chegada else "",
                'forma_pg': item.forma_pg if item.forma_pg else "",
                'frete': item.frete if item.frete else "",
                'parcela': item.parcela if item.parcela else "",
                'vencimento': item.vencimento if item.vencimento else "",
                'pagamento': item.data_pg if item.data_pg else "",
                'desconto': item.desconto if item.desconto else Decimal('0.00'),
                'acrescimo': item.acrescimo if item.acrescimo else Decimal('0.00'),
                'total_pg': (item.valor + item.acrescimo - item.desconto) if item.valor else Decimal('0.00'),
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
                'os': compra.os if compra.os else None,
                'data_pg': compra.data_pg if compra.data_pg else None,
                'valor': float(compra.valor) if compra.valor else 0.00,
                'acrescimo': float(compra.acrescimo) if compra.acrescimo else 0.00,
                'desconto': float(compra.desconto) if compra.desconto else 0.00,
                'vencimento': compra.vencimento if compra.vencimento else None,
                'parcela': compra.parcela if compra.parcela else "",
                'forma_pg': compra.forma_pg if compra.forma_pg else "",
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


from django.shortcuts import get_object_or_404

@login_required(login_url='/')
def cadastrar_produtos(request):
    nome_usuario = request.user.username
    produtos = Produtos.objects.all()
    max_id = produtos.aggregate(Max('id'))['id__max']
    max_id = (max_id + 1) if max_id is not None else 1
    marcas = MarcaProduto.objects.all().order_by('nome')
    categorias = Categoria.objects.all().order_by('nome')
    uni_medida = UnidadeMedida.objects.all().order_by('nome')
    id = request.POST.get('id_produto')
    context = {'max_id': max_id, 'id': id, 'marcas': marcas, 'categorias': categorias, 'uni_medida': uni_medida, 'nome_usuario': nome_usuario}
    if request.method == "POST":
        id = request.POST.get('id_produto')
        # Verifica se o produto já existe
        if Produtos.objects.filter(id=id).exists():
            print(2)    
            produto = Produtos.objects.get(id=id)
            context = {'max_id': max_id, 'produto': produto, 'marcas': marcas, 'id': id, 'categorias': categorias, 'uni_medida': uni_medida}
        
        if request.POST.get('action'):
            print(3)    
            dados = request.POST.dict()
            imagem = request.FILES.get('imagem', None)
            nome = (dados.get('nome') or "").strip()
            
            # Verificar se os ids das chaves estrangeiras são válidos
            categoria_id = dados.get('categoria')
            categoria = get_object_or_404(Categoria, id=categoria_id) if categoria_id else None  # Pode ser None se não for obrigatório
            
            marca_id = dados.get('marca')
            marca = get_object_or_404(MarcaProduto, id=marca_id) if marca_id else None  # Pode ser None se não for obrigatório
            print(marca)
            descricao = dados.get('descricao') or ""
            preco = dados.get('preco') or "0.00"  # Garantir que o valor seja válido
            try:
                preco = float(preco.replace(',', '.'))
            except ValueError:
                preco = 0.00  # Valor padrão para erro de conversão
            
            obs = dados.get('obs') or ""
            
            uni_med_id = dados.get('unidade_medida')
            uni_med = get_object_or_404(UnidadeMedida, id=uni_med_id) if uni_med_id else None  # Pode ser None se não for obrigatório
            
            peso = dados.get('peso') or "0.00"
            try:
                peso = float(peso.replace(',', '.'))
            except ValueError:
                peso = 0.00  # Valor padrão para erro de conversão
                
            dimensoes = dados.get('dimensoes') or "0 x 0 x 0"
            cod_barras = dados.get('cod_barras') or "0"

            # Se o produto já existe, apenas atualize
            if Produtos.objects.filter(id=id).exists():
                print(5)    
                produto = Produtos.objects.get(id=id)
                if imagem:
                    produto.imagem = imagem or produto.imagem
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
                # Caso contrário, cria o produto
                print(4)    
                # produto = Produtos.objects.create(cod_produto=id, imagem=imagem, nome=nome, categoria=categoria, marca=marca)
                produto = Produtos.objects.create(cod_produto=id, imagem=imagem, nome=nome, categoria=categoria, marca=marca, descricao=descricao,
                                                  preco_venda=preco, obs=obs, unidade_medida=uni_med, peso=peso, dimensoes=dimensoes, 
                                                  codigo_barras=cod_barras, usuario=nome_usuario
                                                )
                context['produto'] = produto

    return render(request, 'cadastrar_produtos.html', context)

@login_required(login_url='/')
def cadastrar_fornecedor(request):
    cpf_cnpj = request.POST.get('cpf_cnpj') if request.POST.get('cpf_cnpj') != None else ""
    nome_usuario = request.user.username        
    context = {'cpf_cnpj': cpf_cnpj, 'nome_usuario': nome_usuario}
    if request.method == "POST":
        if Fornecedor.objects.filter(cpf_cnpj=cpf_cnpj).exists():
            fornecedor = Fornecedor.objects.get(cpf_cnpj=cpf_cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                fornecedor.nome = request.POST.get('nome', '').upper()
                fornecedor.endereco = request.POST.get('endereco', '').upper()
                fornecedor.telefone = request.POST.get('telefone') or '(00) 0 0000-0000'
                fornecedor.whatsapp = request.POST.get('whatsapp') or '(00) 0 0000-0000'
                fornecedor.email = request.POST.get('email') or 'sem email cadastrado'
                fornecedor.save()
        else:
            fornecedor = Fornecedor.objects.filter(cpf_cnpj=cpf_cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                nome = request.POST.get('nome', '').upper()
                endereco = request.POST.get('endereco', '').upper()
                telefone = request.POST.get('telefone') or '(00) 0 0000-0000'
                whatsapp = request.POST.get('whatsapp') or '(00) 0 0000-0000'
                email = request.POST.get('email') or 'sem email cadastrado'
                if nome and endereco and telefone and email and whatsapp and cpf_cnpj:
                    fornecedor = Fornecedor.objects.get_or_create(nome=nome, cpf_cnpj=cpf_cnpj, endereco=endereco, telefone=telefone, whatsapp=whatsapp, email=email)
                fornecedor = Fornecedor.objects.get(cpf_cnpj=cpf_cnpj)# if Fornecedor.objects.get(cpf_cnpj=cpf_cnpj).exists() else ""
        context = {
            'cpf_cnpj': cpf_cnpj,
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
    cpf_cnpj = request.POST.get('cpf_cnpj') if request.POST.get('cpf_cnpj') != None else ""
    nome_usuario = request.user.username
    context = {'cpf_cnpj': cpf_cnpj, 'nome_usuario':nome_usuario}

    if request.method == "POST":
        dados = request.POST.dict()
        if Cliente.objects.filter(cpf_cnpj=cpf_cnpj).exists():
            cliente = Cliente.objects.get(cpf_cnpj=cpf_cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:                
                cliente.nome = request.POST.get('nome', '').upper()
                cliente.endereco = request.POST.get('endereco', '').upper()
                cliente.telefone = request.POST.get('telefone') or '(00) 0 0000-0000'
                cliente.whatsapp = request.POST.get('whatsapp') or '(00) 0 0000-0000'
                cliente.email = request.POST.get('email')  or 'sem email cadastrado'
                cliente.save()
        else:
            cliente = Cliente.objects.filter(cpf_cnpj=cpf_cnpj)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                nome = request.POST.get('nome', '').upper()
                endereco = request.POST.get('endereco', '').upper()
                telefone = request.POST.get('telefone') or '(00) 0 0000-0000'
                whatsapp = request.POST.get('whatsapp') or '(00) 0 0000-0000'
                email = request.POST.get('email') or 'sem email cadastrado'
                if nome and endereco and telefone and email and whatsapp and cpf_cnpj:
                    cliente = Cliente.objects.get_or_create(nome=nome, cpf_cnpj=cpf_cnpj, endereco=endereco, telefone=telefone, whatsapp=whatsapp, email=email)
                cliente = Cliente.objects.get(cpf_cnpj=cpf_cnpj)
        
        context = {
            'cpf_cnpj': cpf_cnpj,
            'nome': cliente.nome if cliente else "", 
            'endereco': cliente.endereco if cliente else "", 
            'telefone': cliente.telefone if cliente else "", 
            'whatsapp': cliente.whatsapp if cliente else "", 
            'email': cliente.email if cliente else "",
            'nome_usuario': nome_usuario,
        }
    return render(request, 'cadastrar_cliente.html', context)

@login_required(login_url='/')
def cadastro_profissionais(request):
    cargos = Cargo.objects.all().order_by('nome')
    context = {'cargos': cargos}

    cpf = request.POST.get('cpf') if request.POST.get('cpf') != None else ""
    nome_usuario = request.user.username
    context = {'cpf': cpf, 'nome_usuario':nome_usuario}
    if request.method == "POST":
        if Profissional.objects.filter(cpf=cpf).exists():
            funcionario = Profissional.objects.get(cpf=cpf)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                funcionario.nome = request.POST.get('nome', '').upper()
                funcionario.cargo = Cargo.objects.get(id=request.POST.get('cargo')) or Cargo.objects.get(id=1)
                funcionario.vt_diario = request.POST.get('vt_diario') or '0'
                funcionario.salario = request.POST.get('salario') or '0'
                funcionario.telefone = request.POST.get('telefone') or '(00) 0 0000-0000'
                funcionario.whatsapp = request.POST.get('whatsapp') or '(00) 0 0000-0000'
                funcionario.email = request.POST.get('email') or 'Sem email cadastrado'
                funcionario.obs = request.POST.get('ons')
                funcionario.save()
        else:
            funcionario = Profissional.objects.filter(cpf=cpf)
            cadastrar = request.POST.get('cadastrar')
            if cadastrar:
                nome = request.POST.get('nome', '').upper()
                cargo = Cargo.objects.get(id=request.POST.get('cargo')) or Cargo.objects.get(id=1)
                vt_diario = request.POST.get('vt_diario') or '0'
                salario = request.POST.get('salario') or '0'
                telefone = request.POST.get('telefone') or '(00) 0 0000-0000'
                whatsapp = request.POST.get('whatsapp') or '(00) 0 0000-0000'
                email = request.POST.get('email') or 'Sem email cadastrado'
                obs = request.POST.get('obs') or ''
                if nome and cpf:
                    funcionario = Profissional.objects.get_or_create(nome=nome, salario=salario, vt_diario=vt_diario, cpf=cpf, cargo=cargo, telefone=telefone, whatsapp=whatsapp, email=email, obs=obs)
                funcionario = Profissional.objects.get(cpf=cpf)
        
        context = {
            'cargos':cargos,
            'cpf': cpf,
            'vt_diario':funcionario.vt_diario if funcionario else "",
            'salario':funcionario.salario if funcionario else "",
            'nome': funcionario.nome if funcionario else "", 
            'cargo': funcionario.cargo if funcionario else "", 
            'telefone': funcionario.telefone if funcionario else "", 
            'whatsapp': funcionario.whatsapp if funcionario else "", 
            'email': funcionario.email if funcionario else "",
            'obs': funcionario.obs if funcionario else "",
            'nome_usuario': nome_usuario,
            }

    return render(request, 'cadastro_profissionais.html', context)

@login_required(login_url='/')
def cadastro_veiculos(request):
    clientes = Cliente.objects.all().order_by('nome')
    marcas = Marca.objects.all().order_by('nome')
    motores = Motor.objects.all().order_by('nome')
    combustivel = ""
    transmissoes = ""
    veiculo = None
    placa = ""
    if request.method == "POST":
        dados = request.POST.dict()
        placa = dados.get('placa', '').upper()
        if Veiculos.objects.filter(placa=placa).exists():
            veiculo = Veiculos.objects.get(placa=placa)
        if request.POST.get('action'):
            cliente = Cliente.objects.filter(id=dados.get('cliente')).first() or Cliente.objects.get(nome='NÃO CADASTRADO')
            marca = Marca.objects.filter(id=dados.get('marca')).first() or Marca.objects.get(id=1)
            motor = Motor.objects.filter(id=dados.get('motor')).first() or Motor.objects.get(id=1)
            ano = int(dados.get('ano') or 0)  # Valor padrão para ano
            combustivel = dados.get('combustivel') or "Não Cadastrado"
            transmissoes = dados.get('transmissoes') or "Não Cadastrado"
            # combustivel = Combustivel.objects.filter(id=dados.get('combustivel')).first() or Combustivel.objects.get(id=1)
            # transmissoes = transmissoes.objects.filter(id=dados.get('transmissoes')).first() or transmissoes.objects.get(id=1)
            if veiculo:
                veiculo.cliente = cliente
                veiculo.marca = marca
                veiculo.ano = ano
                veiculo.combustivel = combustivel
                veiculo.transmissao = transmissoes
                veiculo.placa = placa
                veiculo.motor = motor
                veiculo.save()
            else:
                veiculo = Veiculos.objects.create(
                    placa=placa,
                    motor=motor,
                    cliente=cliente,
                    marca=marca,
                    ano=ano,
                    combustivel=combustivel,
                    transmissao=transmissoes
                )
    context = {
        'clientes': clientes,
        'marcas': marcas,
        'motores': motores,
        'combustiveis': combustivel,
        'transmissoes': transmissoes,
        'veiculo': veiculo,
        'placa': placa
    }
    return render(request, 'cadastro_veiculos.html', context)

@login_required(login_url='/')
def controle_estoque(request, ordenar_por="id"):
    produtos = Produtos.objects.all()
    compras = Caixa_compra.objects.filter(status=True)
    vendas = OS_Produto.objects.filter(status=True)
    relatorio = []
    dias = 7
    dias_atras = timezone.now() - timedelta(days=7)
    if request.method == "POST":
        dias = request.POST.get('quant_vend_ult_dias')
        dias_atras = timezone.now() - timedelta(days=int(dias))
    vendas_ultimos_dias = Contas_receber.objects.filter(data_finalizacao__gte=dias_atras)
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

        caixa_ult_venda = OS_Produto.objects.filter(produto=item, status=True).last()
        if caixa_ult_venda:
            ultima_venda = Contas_receber.objects.filter(os=caixa_ult_venda.os).first()
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
            for caixa_venda in OS_Produto.objects.filter(produto=item, os=venda.os)
        )
        relatorio.append({
            'id': item.id,
            'produto': item.nome,
            'marca': item.marca,
            'categoria': item.categoria,
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

@login_required(login_url='/')
def controle_servico(request, ordenar_por="id"):
    nome_usuario = request.user.username
    servicos = TipoServicos.objects.all()
    os = OS.objects.all()
    relatorio = []
    for item in servicos:
        quant_realizados = 0
        valor_recebido = 0
        # modelos de carros com maior numero de reparos
        mod_carr_maior_reparo = 0
        servicos_realizados = os.filter(servico=item)
        veiculos = Veiculos.objects.all()
        for item2 in servicos_realizados:
            quant_realizados += 1
            valor_recebido += item2.total
            for veiculo in veiculos:
                mod_carr_maior_reparo + 0
                if veiculo.marca == item2.veiculo.marca:
                     mod_carr_maior_reparo += 1
        print(F'{item.nome} - {quant_realizados} - R$ {valor_recebido} - {mod_carr_maior_reparo}')
    context = {'servicos':servicos,

                }
    return render(request, 'controle_estoque.html', context)


@login_required(login_url='/')
def rel_cliente(request):
    nome_usuario = request.user.username
    clientes = Cliente.objects.order_by('nome')
    faturamento = 0
    clientes_info = []
    for cliente in clientes:
        contas = Contas_receber.objects.filter(pagador=cliente)
        faturamento = sum(conta.valor for conta in contas)
        clientes_info.append({
            'cliente': cliente,
            'faturamento':faturamento,
        })

    context = {'clientes_info':clientes_info,
                'nome_usuario': nome_usuario, }
    return render(request, 'rel_cliente.html', context)

@login_required(login_url='/')
def rel_fornecedor(request):
    nome_usuario = request.user.username
    fornecedores = Fornecedor.objects.order_by('nome')
    faturamento = 0
    fornecedor_info = []
    for fornecedor in fornecedores:
        contas = Contas_a_pagar.objects.filter(fornecedor=fornecedor)
        faturamento = sum(conta.valor for conta in contas)
        fornecedor_info.append({
            'fornecedor': fornecedor,
            'faturamento':faturamento,
        })

    context = {'fornecedor_info':fornecedor_info,
                'nome_usuario': nome_usuario, }
    return render(request, 'rel_fornecedor.html', context)

@login_required(login_url='/')
def rel_produto(request):
    nome_usuario = request.user.username
    produtos = Produtos.objects.order_by('nome')
    faturamento = 0
    produto_info = []
    for produto in produtos:
        contas = OS_Produto.objects.filter(produto=produto)
        faturamento = sum(conta.total for conta in contas)
        produto_info.append({
            'produto': produto,
            'faturamento':faturamento,
        })
    context = {'produto_info':produto_info,
                'nome_usuario': nome_usuario, }
    return render(request, 'rel_produto.html', context)

@login_required(login_url='/')
def rel_veiculo(request):
    nome_usuario = request.user.username
    veiculos = Veiculos.objects.all()
    faturamento = 0
    veiculo_info = []
    for veiculo in veiculos:
        contas = OS.objects.filter(veiculo=veiculo)
        faturamento = sum(conta.total for conta in contas)
        veiculo_info.append({
            'veiculo': veiculo,
            'faturamento':faturamento,
        })
    context = {'veiculo_info':veiculo_info,
                'nome_usuario': nome_usuario, }
    return render(request, 'rel_veiculo.html', context)

@login_required(login_url='/')
def rel_funcionario(request):
    nome_usuario = request.user.username
    funcionarios = Profissional.objects.all()
    faturamento = 0
    funcionario_info = []
    for funcionario in funcionarios:
        contas = OS.objects.filter(profissional=funcionario)
        faturamento = sum(conta.total for conta in contas)
        funcionario_info.append({
            'funcionario': funcionario,
            'faturamento':faturamento,
        })
    context = {'funcionario_info':funcionario_info,
                'nome_usuario': nome_usuario, }
    return render(request, 'rel_funcionario.html', context)

@login_required(login_url='/')
def rel_servico(request):
    nome_usuario = request.user.username
    servicos = TipoServicos.objects.all()
    
    # Processa os dados de faturamento e carros associados para cada serviço
    servico_info = []
    for servico in servicos:
        contas = OS.objects.filter(servico=servico)
        quant_servicos = contas.count()
        faturamento = contas.aggregate(Sum('total'))['total__sum'] or 0

        # Determina os carros mais frequentes para este serviço
        carros = (
            contas
            .values('veiculo__marca__nome', 'veiculo__marca__modelo')
            .annotate(total=Count('id'))
            .order_by('-total')[:3]  # Pega os 3 carros mais frequentes
        )

        # Formata os carros para exibição no template
        carros_info = [f"{carro['veiculo__marca__nome']} {carro['veiculo__marca__modelo']}" for carro in carros]

        servico_info.append({
            'servico': servico,
            'faturamento': faturamento,
            'carros': carros_info,
            'quant_servicos':quant_servicos,
        })

    context = {
        'servico_info': servico_info,
        'nome_usuario': nome_usuario,
    }

    return render(request, 'rel_servico.html', context)

@login_required(login_url='/')
def folha_pagamento(request):
    nome_usuario = request.user.username
    funcionarios = Profissional.objects.order_by('nome')
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    mes_ano = str(mes_atual) + '/' + str(ano_atual)
    quant_dias = Dias_uteis.objects.filter(mes_ano=mes_ano).values_list('quant_dias', flat=True).first()
    va = 0
    va = 20 * quant_dias # V.A = 20 reais por dia
    relatorio = []
    for item in funcionarios:
        salario = Decimal(item.salario)
        if salario <= Decimal('1518.00'):
            inss = salario * Decimal('0.075')
        elif salario <= Decimal('2793.88'):
            inss = salario * Decimal(0.09)
        elif salario <= Decimal('4190.83') :
            inss = salario * Decimal(0.012)
        elif salario <= Decimal('8157.41'):
            inss = salario * Decimal(0.014)
        else:
            inss = 'Verificar'
            inss = 'Verificar'

        
        if salario <= Decimal('2259.20') :
            irrf = Decimal('0.00')
        elif salario <= Decimal('2828.65'):
            irrf = salario * Decimal('0.075')
        elif salario <= Decimal('3751.05'):
            irrf = salario * Decimal('0.15')
        elif salario <= Decimal('4664.68'):
            irrf = salario * Decimal('0.225')
        else:
            irrf = salario * Decimal('0.275')
        vt = 0
        if quant_dias:
            vt = item.vt_diario * quant_dias

        desconto_vt = salario * Decimal('0.06')

        fgts = str(round(salario * Decimal('0.07'), 2)).replace('.',',')
        salario_liquido = Decimal(salario - inss - desconto_vt - irrf)
        # -INSS - IRRF
        desconto_vt = str(round(desconto_vt, 2)).replace('.',',')
        inss = str(round(inss, 2)).replace('.',',')
        irrf = str(round(irrf, 2)).replace('.',',')
        salario_liquido = str(round(salario_liquido, 2)).replace('.',',')
        folha = Folha_pagamento.objects.get(mes_ano_competencia=mes_ano, funcionario=item)
        relatorio.append({
            'funcionario': item,
            'inss': folha.inss if folha.inss else inss,
            'irrf': folha.irrf if folha.irrf else irrf,
            'desconto_vt': folha.desconto_vt if folha.desconto_vt else desconto_vt,
            'salario_liquido': folha.salario_liquido if folha.salario_liquido else salario_liquido,
            'dias_extras': folha.dias_extras if folha.dias_extras else 0,
            'va': folha.va if folha.va else va,
            'vt': folha.vt if folha.vt else vt,
            'pg_va_vt': folha.pg_va_vt if folha.pg_va_vt else '',
            'fgts': folha.fgts if folha.fgts else fgts,
            'obs': folha.obs if folha.obs else '',
        })


    if request.method == "POST":
        dados = request.POST.dict()
        if dados.get('acao') == 'Gravar':
            mes = dados.get('mes') 
            ano = dados.get('ano')
            mes_ano = mes + '/' + ano
            quant_dias = Decimal(dados.get('quant_dias'))
            if not Dias_uteis.objects.filter(mes_ano=mes_ano).exists():
                dias_uteis = Dias_uteis.objects.create(mes_ano=mes_ano, quant_dias=quant_dias)
        elif dados.get('acao') == 'Pagamento Salário':
            print(dados)
            mes = dados.get('mes') 
            ano = dados.get('ano')
            mes_ano = f"{str(mes)}/{ano}"

            for chave, valor in dados.items():
                if chave.startswith('funcionario'):
                    funcionario = funcionarios.get(id=valor)

                    folha, created = Folha_pagamento.objects.get_or_create(
                            funcionario=funcionario,
                            mes_ano_competencia=mes_ano,  
                            defaults={
                                'salario_bruto':funcionario.salario,
                                'inss': va,
                                'vt': vt,
                                'pg_va_vt': pg_va_vt
                            }
                        )

        elif dados.get('acao') == 'Pagamento Vales':
            mes = dados.get('mes') 
            ano = dados.get('ano')
            mes_ano = f"{str(mes)}/{ano}"
            pg_va_vt = dados.get('pg_va_vt', '')
            
            # print(dias_extras)

            dias_uteis = Dias_uteis.objects.get(mes_ano=mes_ano)
            for chave, valor in dados.items():
                if chave.startswith('funcionario'):
                    funcionario = funcionarios.get(id=valor)
                    dias_extras_key = f'dias_extras{valor}'  # Construir a chave
                    dias_extras = Decimal(dados.get(dias_extras_key, 0))  # Recuperar o valor de 'dias_extras'

                    vt = Decimal(funcionario.vt_diario * dias_uteis.quant_dias) + Decimal(funcionario.vt_diario * dias_extras)
                    va = Decimal(20 * dias_uteis.quant_dias) + Decimal(20 * dias_extras) # V.A = 20 REAIS POR DIA
                    folha, created = Folha_pagamento.objects.get_or_create(
                            funcionario=funcionario,
                            mes_ano_competencia=mes_ano,  
                            defaults={
                                'dias_extras':dias_extras,
                                'va': va,
                                'vt': vt,
                                'pg_va_vt': pg_va_vt
                            }
                        )
                    if not created:
                        folha.dias_extras = dias_extras
                        folha.va = va
                        folha.vt = vt
                        folha.pg_va_vt = pg_va_vt
                        folha.save()




            # print(dados)
    context = {
        'nome_usuario': nome_usuario,
        'relatorio': relatorio,
        'mes_atual':mes_atual,
        'ano_atual':ano_atual,
        'quant_dias':quant_dias,
        
        # 'previsao_salario': previsao_salario,
        # 'previsao_vv':previsao_vv,
    }
    return render(request, 'folha_pagamento.html', context)

@login_required(login_url='/')
def os_por_cliente(request, cnpj):
    nome_usuario = request.user.username
    cliente = Cliente.objects.get(cpf_cnpj=cnpj)
    os_ids = Contas_receber.objects.filter(pagador=cliente).values_list('os', flat=True)
    os = OS.objects.filter(os__in=os_ids)
    os_produtos = OS_Produto.objects.filter(os__in=os_ids)
    context = {'os': os, 'os_produtos': os_produtos, 'nome_usuario': nome_usuario}
    return render(request, 'os_por_cliente.html', context)

@login_required(login_url='/')
def compra_por_fornecedor(request, cnpj):
    nome_usuario = request.user.username
    fornecedor = Fornecedor.objects.get(cpf_cnpj=cnpj)
    os_ids = Contas_a_pagar.objects.filter(fornecedor=fornecedor).values_list('os', flat=True)
    caixa_compra = Caixa_compra.objects.filter(os__in=os_ids)
    return render(request, 'compra_por_fornecedor.html', {'caixa_compra':caixa_compra, 'nome_usuario': nome_usuario})

@login_required(login_url='/')
def servicos_por_veiculo(request, placa):
    nome_usuario = request.user.username
    veiculo = Veiculos.objects.get(placa=placa)
    os = OS.objects.filter(veiculo=veiculo)
    # os = OS.;objects.filter(os__in=os_ids)
    return render(request, 'servicos_por_veiculo.html', {'os': os, 'nome_usuario':nome_usuario})

@login_required(login_url='/')
def servicos_por_funcionario(request, cpf):
    nome_usuario = request.user.username
    funcionario = Profissional.objects.get(cpf=cpf)
    os = OS.objects.filter(profissional=funcionario)
    return render(request, 'servicos_por_funcionario.html', {'os': os, 'nome_usuario':nome_usuario})
########################################### Dasboard ###########################################

def grafico_forma_pg(anos, meses):
    forma_pg = {
        'BOLETO': 'Boleto',
        'CREDITO': 'Cartão de Crédito',
        'DEBITO': 'Cartão de Débito',
        'DINHEIRO': 'Dinheiro',
        'PIX': 'PIX/Transferência'
        }
    labels = []
    dados_grafico_rosca = []
    for item in forma_pg:
        quant = Contas_receber.objects.filter(
            forma_pg=item,
            data_finalizacao__year__in=anos,  # Filtra por anos selecionados
            data_finalizacao__month__in=meses  # Filtra por meses selecionados
        ).count()

        if quant > 0:
            labels.append(item)
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
    vendas = Contas_receber.objects.filter(
                                  data_finalizacao__year__in=anos,
                                  )

    # Criar um dicionário para armazenar o total por mês
    total_por_mes = {}
    for venda in vendas:
        mes = venda.data_finalizacao.month  # Obter o mês da data de finalização
        if mes in total_por_mes:
            total_por_mes[mes] += venda.valor  # Somar o total ao mês existente
        else:
            total_por_mes[mes] = venda.valor  # Inicializar o total para o mês

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
    vendas = OS_Produto.objects.filter(
                                        data_cadastro__year__in=anos,
                                        data_cadastro__month__in=meses_selecionados)
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
    vendas = OS_Produto.objects.filter(data_cadastro__year__in=anos,
                                  data_cadastro__month__in=meses_selecionados)
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
    vendas = OS_Produto.objects.filter(data_cadastro__year__in=anos,
                                  data_cadastro__month__in=meses_selecionados)
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
    vendas = OS_Produto.objects.filter(data_cadastro__year__in=anos,
                                  data_cadastro__month__in=meses_selecionados)
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
    vendas = OS_Produto.objects.filter(data_cadastro__year__in=anos,
                                  data_cadastro__month__in=meses_selecionados)
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

@login_required(login_url='/')
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

    vendas = Contas_receber.objects.all()
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



