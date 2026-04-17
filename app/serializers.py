from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers

from .models import (
    Estacionamento,
    Fiscal,
    Multa,
    Pagamento,
    Usuario,
    Vaga,
    Veiculo,
)


class UsuarioResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'pontos', 'criado_em']


class VeiculoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = ['id', 'placa', 'modelo', 'cor']


class VagaResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaga
        fields = [
            'id',
            'numero',
            'rua',
            'regiao',
            'descricao',
            'latitude',
            'longitude',
            'preco_hora',
            'status',
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    veiculos = VeiculoResumoSerializer(many=True, read_only=True)
    senha = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Usuario
        fields = ['id', 'nome', 'email', 'senha', 'pontos', 'criado_em', 'veiculos']
        read_only_fields = ['id', 'pontos', 'criado_em']

    def create(self, validated_data):
        validated_data['senha'] = make_password(validated_data['senha'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        senha = validated_data.pop('senha', None)
        if senha:
            instance.senha = make_password(senha)

        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            usuario = Usuario.objects.get(email=attrs['email'])
        except Usuario.DoesNotExist as exc:
            raise serializers.ValidationError('E-mail ou senha invalidos.') from exc

        senha_valida = check_password(attrs['senha'], usuario.senha)
        senha_legada_valida = usuario.senha and attrs['senha'] == usuario.senha

        if not senha_valida and not senha_legada_valida:
            raise serializers.ValidationError('E-mail ou senha invalidos.')

        attrs['usuario'] = usuario
        return attrs


class VeiculoSerializer(serializers.ModelSerializer):
    usuario_detalhes = UsuarioResumoSerializer(source='usuario', read_only=True)

    class Meta:
        model = Veiculo
        fields = ['id', 'placa', 'modelo', 'cor', 'usuario', 'usuario_detalhes']

    def validate_placa(self, value):
        return value.upper()


class VagaSerializer(serializers.ModelSerializer):
    esta_disponivel = serializers.SerializerMethodField()

    class Meta:
        model = Vaga
        fields = [
            'id',
            'numero',
            'rua',
            'regiao',
            'descricao',
            'latitude',
            'longitude',
            'preco_hora',
            'status',
            'esta_disponivel',
            'criada_em',
            'atualizada_em',
        ]
        read_only_fields = ['criada_em', 'atualizada_em']

    def get_esta_disponivel(self, obj):
        return obj.status == Vaga.LIVRE


class PagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pagamento
        fields = [
            'id',
            'estacionamento',
            'valor',
            'tempo_comprado',
            'forma_pagamento',
            'data_pagamento',
        ]
        read_only_fields = ['id']


class EstacionamentoSerializer(serializers.ModelSerializer):
    veiculo_detalhes = VeiculoResumoSerializer(source='veiculo', read_only=True)
    vaga_detalhes = VagaResumoSerializer(source='vaga', read_only=True)
    pagamentos = PagamentoSerializer(many=True, read_only=True)
    tempo_restante_segundos = serializers.SerializerMethodField()

    class Meta:
        model = Estacionamento
        fields = [
            'id',
            'veiculo',
            'veiculo_detalhes',
            'vaga',
            'vaga_detalhes',
            'hora_inicio',
            'hora_fim',
            'status',
            'tempo_restante_segundos',
            'pagamentos',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']

    def get_tempo_restante_segundos(self, obj):
        if not obj.hora_fim or obj.status != Estacionamento.ATIVO:
            return 0

        from django.utils import timezone

        restante = obj.hora_fim - timezone.now()
        return max(0, int(restante.total_seconds()))

    def validate(self, attrs):
        vaga = attrs.get('vaga', getattr(self.instance, 'vaga', None))

        if vaga and vaga.status != Vaga.LIVRE and not self.instance:
            raise serializers.ValidationError({'vaga': 'Esta vaga nao esta disponivel.'})

        return attrs


class IniciarEstacionamentoSerializer(serializers.Serializer):
    veiculo = serializers.PrimaryKeyRelatedField(queryset=Veiculo.objects.all())
    vaga = serializers.PrimaryKeyRelatedField(queryset=Vaga.objects.all())
    tempo_minutos = serializers.IntegerField(min_value=1, required=False)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    forma_pagamento = serializers.ChoiceField(
        choices=Pagamento.FORMA_CHOICES,
        required=False,
        default=Pagamento.PIX,
    )

    def validate_vaga(self, value):
        if value.status != Vaga.LIVRE:
            raise serializers.ValidationError('Esta vaga nao esta disponivel.')
        return value

    def validate(self, attrs):
        tempo_minutos = attrs.get('tempo_minutos')

        if tempo_minutos and 'valor' not in attrs:
            raise serializers.ValidationError(
                {'valor': 'Informe o valor ao iniciar com tempo comprado.'}
            )

        return attrs


class ConfirmarPagamentoSerializer(serializers.Serializer):
    tempo_minutos = serializers.IntegerField(min_value=1)
    valor = serializers.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = serializers.ChoiceField(choices=Pagamento.FORMA_CHOICES)


class RenovarEstacionamentoSerializer(ConfirmarPagamentoSerializer):
    pass


class FiscalSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Fiscal
        fields = ['id', 'nome', 'login', 'senha']

    def create(self, validated_data):
        validated_data['senha'] = make_password(validated_data['senha'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        senha = validated_data.pop('senha', None)
        if senha:
            instance.senha = make_password(senha)

        return super().update(instance, validated_data)


class MultaSerializer(serializers.ModelSerializer):
    estacionamento_detalhes = EstacionamentoSerializer(
        source='estacionamento',
        read_only=True,
    )
    fiscal_detalhes = FiscalSerializer(source='fiscal', read_only=True)

    class Meta:
        model = Multa
        fields = [
            'id',
            'estacionamento',
            'estacionamento_detalhes',
            'fiscal',
            'fiscal_detalhes',
            'valor',
            'data_multa',
            'status',
        ]
