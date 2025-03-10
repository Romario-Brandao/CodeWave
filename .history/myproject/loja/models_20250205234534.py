from django.db import models
from datetime import date, datetime


# Create your models here.

class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.id} - {self.nome}'
    
class Cargo(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.id} - {self.nome}'
    
class UnidadeMedida(models.Model):  # Renomeado para usar PascalCase (padrão Python)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.id} - {self.nome}'

class MarcaProduto(models.Model):
    nome = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.id} - {self.nome}'

class Marca(models.Model):
    nome = models.CharField(max_length=20)
    modelo = models.CharField(max_length=20, null=True, blank=True, default="")

    def __str__(self):
        return f'{self.id} - {self.nome} - Modelo: {self.modelo}'

class Motor(models.Model):
    nome = models.CharField(max_length=20, default="")

    def __str__(self):
        return f'{self.id} - {self.nome}'

class Combustivel(models.Model):
    nome = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.id} - {self.nome}'

class Transmissao(models.Model):
    nome = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.id} - {self.nome}'
    
class Status(models.Model):
    nome = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.id} - {self.nome}'
    
class TipoServicos(models.Model):
    nome = models.CharField(max_length=200)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.id} - {self.nome}: R$ {self.valor}'

class Cliente(models.Model):
    nome = models.CharField(max_length=30)
    cpf_cnpj = models.CharField(max_length=14, unique=True)
    endereco = models.CharField(max_length=100,null=True, blank=True)
    telefone = models.CharField(max_length=16)
    whatsapp = models.CharField(max_length=16)
    email = models.EmailField()
    obs = models.CharField(max_length=300, null=True, blank=True)
    data_cadastro = models.DateField(default=date.today)

    def __str__(self):
        return f'{self.id} - {self.nome}'
    
class Fornecedor(models.Model):
    nome = models.CharField(max_length=30)
    cpf_cnpj = models.CharField(max_length=14, unique=True)        
    endereco = models.CharField(max_length=100,null=True, blank=True)
    telefone = models.CharField(max_length=16)
    whatsapp = models.CharField(max_length=16)
    email = models.EmailField()
    obs = models.CharField(max_length=300, null=True, blank=True)
    data_cadastro = models.DateField(default=date.today)

    def __str__(self):
        return f'{self.id} - {self.nome}'
    
class Profissional(models.Model):
    nome = models.CharField(max_length=30)
    cpf = models.CharField(max_length=14, unique=True)
    cargo = models.ForeignKey(Cargo, null=True, blank=True, on_delete=models.SET_NULL)
    salario = models.DecimalField(default=0, max_digits=10,  decimal_places=2)
    telefone = models.CharField(max_length=16)
    whatsapp = models.CharField(max_length=16)
    email = models.EmailField(null=True, blank=True)
    obs = models.CharField(max_length=300, null=True, blank=True)
    data_cadastro = models.DateField(default=date.today)
    ativo = models.BooleanField(default=True)
    vt_diario = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.id} - {self.nome} - {self.salario}'

class Veiculos(models.Model):
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL)
    marca = models.ForeignKey(Marca, null=True, blank=True, on_delete=models.SET_NULL)
    ano = models.CharField(max_length=20)
    motor = models.ForeignKey(Motor, null=True, blank=True, on_delete=models.SET_NULL)
    combustivel = models.CharField(max_length=20, null=False, blank=False)
    transmissao = models.CharField(max_length=20, null=False, blank=False)
    placa = models.CharField(max_length=10, null=False, blank=False)
    data_cadastro = models.DateField(default=date.today)

    def __str__(self):
        return f'{self.id} - {self.cliente.nome} - {self.marca.nome} - {self.marca.modelo} - {self.ano} - {self.motor} - {self.placa}'

class Produtos(models.Model):
    imagem = models.ImageField(null=True, blank=True)
    cod_produto = models.IntegerField(null=True, blank=True)
    nome = models.CharField(max_length=200) 
    descricao = models.CharField(max_length=200, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, null=True, blank=True, on_delete=models.SET_NULL)
    marca = models.ForeignKey(MarcaProduto, null=True, blank=True, on_delete=models.SET_NULL)
    preco_venda = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estoque = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    unidade_medida = models.ForeignKey(UnidadeMedida, null=True, blank=True, on_delete=models.SET_NULL)  # Corrigido o nome
    data_cadastro = models.DateField(default=date.today)
    codigo_barras = models.IntegerField(null=True, blank=True)
    peso = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) 
    dimensoes = models.CharField(max_length=10, null=True, blank=True)
    obs = models.CharField(max_length=100, null=True, blank=True)
    usuario = models.CharField(max_length=20, null=True, blank=True, default="")

    def __str__(self):
        return f"Produto: {self.nome} - Valor: R$ {self.preco_venda}"

class OS(models.Model):
    os = models.DecimalField(max_digits=100, decimal_places=0, default=0)
    data_cadastro = models.DateTimeField(default=datetime.now)
    servico = models.ForeignKey(TipoServicos, null=True, blank=True, on_delete=models.SET_NULL)
    acrescimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    veiculo = models.ForeignKey(Veiculos, null=True, blank=True, on_delete=models.SET_NULL)
    profissional = models.ForeignKey(Profissional, null=True, blank=True, on_delete=models.SET_NULL)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.BooleanField(default=False)
    obs = models.CharField(null=True, blank=True, max_length=20)

    def __str__(self):
        return f"Finalizado: {self.status} - {self.os}"


class OS_Produto(models.Model):
    os = models.DecimalField(max_digits=100, decimal_places=0, default=0)
    data_cadastro = models.DateTimeField(default=datetime.now)
    produto = models.ForeignKey(Produtos, null=True, blank=True, on_delete=models.SET_NULL)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Finalizado: {self.status} - {self.os}"

class Contas_receber(models.Model):
    os = models.DecimalField(max_digits=100, decimal_places=0, default=0)
    data_finalizacao =  models.DateTimeField(default=datetime.now)
    parcela = models.CharField(max_length=10)
    forma_pg = models.CharField(max_length=10)
    pagador = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vencimento = models.DateTimeField(null=False, blank=False)
    obs = models.CharField(max_length=50)
    data_pg = models.DateField(null=True, blank=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    acrescimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"OS {self.os} - {self.parcela} {self.forma_pg} {self.pagador.nome} {self.valor}"
    
    
class Contas_a_pagar(models.Model):
    os = models.DecimalField(max_digits=100, decimal_places=0, default=0)
    nf = models.IntegerField(null=True, blank=True)
    data_finalizacao =  models.DateTimeField(default=datetime.now)
    parcela = models.CharField(max_length=10)
    forma_pg = models.CharField(max_length=10)
    fornecedor = models.ForeignKey(Fornecedor, null=True, blank=True, on_delete=models.SET_NULL)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vencimento = models.DateTimeField(null=False, blank=False)
    obs = models.CharField(max_length=50)
    data_pg = models.DateField(null=True, blank=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    acrescimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    data_compra = models.DateField(null=True, blank=True)  # Data da compra
    data_chegada = models.DateField(null=True, blank=True)  # Data de chegada do produto
    frete = models.CharField(max_length=3, null=True, blank=True) # Frete CIF ou FOB ou RET(Retirada)
    usuario = models.CharField(max_length=20, null=True, blank=True, default="")

    def __str__(self):
        return f"OS {self.os} - {self.parcela} {self.forma_pg} {self.pagador.nome} {self.valor}"
    
class Caixa_compra(models.Model):
    os = models.DecimalField(max_digits=100, decimal_places=0, default=0)
    data_cadastro = models.DateTimeField(default=datetime.now)
    produto = models.ForeignKey(Produtos,  null=True, blank=True, on_delete=models.SET_NULL)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    valor_uni = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.BooleanField(default=False)


    def __str__(self):
        return f"Caixa: {self.caixa_aberto}- Produto: {self.produto.nome} - Finalizado: {self.finalizado}"
    
class Folha_pagamento(models.Model):
    funcionario = models.ForeignKey(Profissional, null=True, blank=True, on_delete=models.SET_NULL)
    mes_ano_competencia = models.CharField(max_length=7, default="")
    salario_bruto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    inss = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    irrf = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto_vt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    salario_liquido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pg_salario = models.DateField(null=True, blank=True)
    dias_extras = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    va = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pg_va_vt = models.DateField(null=True, blank=True)
    fgts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    obs = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"Compensação: {self.mes_ano_competencia} - Funcionario: {self.funcionario.nome} - V.A: {self.va} VT: {self.vt} - Data: VA + VT: {self.pg_va_vt}"


class Dias_uteis(models.Model):
    mes_ano = models.CharField(max_length=7, unique=True)
    quant_dias = models.DecimalField(default=0, decimal_places=0, max_digits=10)

    def __str__(self):
        return f"{self.mes_ano} - {self.quant_dias}"
