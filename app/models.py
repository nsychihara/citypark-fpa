from django.db import models


class Usuario(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255, blank=True, default='')
    pontos = models.PositiveIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    modelo = models.CharField(max_length=50)
    cor = models.CharField(max_length=30, blank=True)
    usuario = models.ForeignKey(
        Usuario,
        db_column='id_usuario',
        on_delete=models.CASCADE,
        related_name='veiculos',
    )

    class Meta:
        db_table = 'veiculos'
        ordering = ['placa']

    def __str__(self):
        return f'{self.placa} - {self.modelo}'


class Vaga(models.Model):
    LIVRE = 'livre'
    OCUPADA = 'ocupada'
    MANUTENCAO = 'manutencao'

    STATUS_CHOICES = [
        (LIVRE, 'Livre'),
        (OCUPADA, 'Ocupada'),
        (MANUTENCAO, 'Manutencao'),
    ]

    numero = models.CharField(max_length=10)
    rua = models.CharField(max_length=100)
    regiao = models.CharField(max_length=30, default='regiao A')
    descricao = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    preco_hora = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=LIVRE)
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vagas'
        ordering = ['rua', 'numero']
        unique_together = ['rua', 'numero']

    def __str__(self):
        return f'{self.rua} - vaga {self.numero}'


class Estacionamento(models.Model):
    ATIVO = 'ativo'
    ENCERRADO = 'encerrado'
    EXPIRADO = 'expirado'

    STATUS_CHOICES = [
        (ATIVO, 'Ativo'),
        (ENCERRADO, 'Encerrado'),
        (EXPIRADO, 'Expirado'),
    ]

    veiculo = models.ForeignKey(
        Veiculo,
        db_column='id_veiculo',
        on_delete=models.CASCADE,
        related_name='estacionamentos',
    )
    vaga = models.ForeignKey(
        Vaga,
        db_column='id_vaga',
        on_delete=models.CASCADE,
        related_name='estacionamentos',
    )
    hora_inicio = models.DateTimeField()
    hora_fim = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=ATIVO)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'estacionamentos'
        ordering = ['-hora_inicio']

    def __str__(self):
        return f'{self.veiculo.placa} em {self.vaga}'


class Pagamento(models.Model):
    PIX = 'pix'
    DEBITO = 'debito'
    CREDITO = 'credito'
    PONTOS = 'pontos'

    FORMA_CHOICES = [
        (PIX, 'Pix'),
        (DEBITO, 'Debito'),
        (CREDITO, 'Credito'),
        (PONTOS, 'Pontos'),
    ]

    estacionamento = models.ForeignKey(
        Estacionamento,
        db_column='id_estacionamento',
        on_delete=models.CASCADE,
        related_name='pagamentos',
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    tempo_comprado = models.PositiveIntegerField(help_text='Tempo comprado em minutos.')
    forma_pagamento = models.CharField(max_length=20, choices=FORMA_CHOICES, default=PIX)
    data_pagamento = models.DateTimeField()

    class Meta:
        db_table = 'pagamentos'
        ordering = ['-data_pagamento']

    def __str__(self):
        return f'{self.estacionamento} - R$ {self.valor}'


class Fiscal(models.Model):
    nome = models.CharField(max_length=100)
    login = models.CharField(max_length=50, unique=True)
    senha = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'fiscais'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Multa(models.Model):
    PENDENTE = 'pendente'
    PAGO = 'pago'

    STATUS_CHOICES = [
        (PENDENTE, 'Pendente'),
        (PAGO, 'Pago'),
    ]

    estacionamento = models.OneToOneField(
        Estacionamento,
        db_column='id_estacionamento',
        on_delete=models.CASCADE,
        related_name='multa',
    )
    fiscal = models.ForeignKey(
        Fiscal,
        db_column='id_fiscal',
        on_delete=models.CASCADE,
        related_name='multas',
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_multa = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDENTE)

    class Meta:
        db_table = 'multas'
        ordering = ['-data_multa']

    def __str__(self):
        return f'Multa {self.estacionamento_id} - {self.status}'
