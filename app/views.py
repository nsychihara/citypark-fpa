from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Estacionamento, Fiscal, Multa, Pagamento, Usuario, Vaga, Veiculo
from .serializers import (
    ConfirmarPagamentoSerializer,
    EstacionamentoSerializer,
    FiscalSerializer,
    IniciarEstacionamentoSerializer,
    LoginSerializer,
    MultaSerializer,
    PagamentoSerializer,
    RenovarEstacionamentoSerializer,
    UsuarioSerializer,
    VagaSerializer,
    VeiculoSerializer,
)


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.prefetch_related('veiculos').all()
    serializer_class = UsuarioSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = serializer.validated_data['usuario']
        estacionamento_ativo = (
            Estacionamento.objects.select_related('veiculo', 'vaga')
            .prefetch_related('pagamentos')
            .filter(veiculo__usuario=usuario, status=Estacionamento.ATIVO)
            .order_by('-hora_inicio')
            .first()
        )

        return Response(
            {
                'usuario': UsuarioSerializer(usuario).data,
                'estacionamento_ativo': EstacionamentoSerializer(estacionamento_ativo).data
                if estacionamento_ativo
                else None,
            }
        )


class VeiculoViewSet(viewsets.ModelViewSet):
    queryset = Veiculo.objects.select_related('usuario').all()
    serializer_class = VeiculoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario_id = self.request.query_params.get('usuario')

        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        return queryset


class VagaViewSet(viewsets.ModelViewSet):
    queryset = Vaga.objects.all()
    serializer_class = VagaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        regiao = self.request.query_params.get('regiao')
        rua = self.request.query_params.get('rua')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if regiao:
            queryset = queryset.filter(regiao__iexact=regiao)
        if rua:
            queryset = queryset.filter(rua__icontains=rua)

        return queryset

    @action(detail=False, methods=['get'])
    def disponiveis(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(status=Vaga.LIVRE))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def resumo(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        livres = queryset.filter(status=Vaga.LIVRE).count()
        ocupadas = queryset.filter(status=Vaga.OCUPADA).count()
        manutencao = queryset.filter(status=Vaga.MANUTENCAO).count()

        return Response(
            {
                'total': total,
                'livres': livres,
                'ocupadas': ocupadas,
                'manutencao': manutencao,
            }
        )


class EstacionamentoViewSet(viewsets.ModelViewSet):
    queryset = (
        Estacionamento.objects.select_related('veiculo', 'veiculo__usuario', 'vaga')
        .prefetch_related('pagamentos')
        .all()
    )
    serializer_class = EstacionamentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario_id = self.request.query_params.get('usuario')
        veiculo_id = self.request.query_params.get('veiculo')
        status_param = self.request.query_params.get('status')

        if usuario_id:
            queryset = queryset.filter(veiculo__usuario_id=usuario_id)
        if veiculo_id:
            queryset = queryset.filter(veiculo_id=veiculo_id)
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset

    @action(detail=False, methods=['get'])
    def ativo(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(status=Estacionamento.ATIVO)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def iniciar(self, request):
        serializer = IniciarEstacionamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        veiculo = serializer.validated_data['veiculo']
        vaga = serializer.validated_data['vaga']
        tempo_minutos = serializer.validated_data.get('tempo_minutos')
        agora = timezone.now()

        estacionamento = Estacionamento.objects.create(
            veiculo=veiculo,
            vaga=vaga,
            hora_inicio=agora,
            hora_fim=agora + timedelta(minutes=tempo_minutos)
            if tempo_minutos
            else None,
            status=Estacionamento.ATIVO,
        )
        vaga.status = Vaga.OCUPADA
        vaga.save(update_fields=['status', 'atualizada_em'])

        if tempo_minutos:
            Pagamento.objects.create(
                estacionamento=estacionamento,
                valor=serializer.validated_data['valor'],
                tempo_comprado=tempo_minutos,
                forma_pagamento=serializer.validated_data['forma_pagamento'],
                data_pagamento=agora,
            )
            veiculo.usuario.pontos += 1
            veiculo.usuario.save(update_fields=['pontos'])

        return Response(
            self.get_serializer(estacionamento).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def confirmar_pagamento(self, request, pk=None):
        estacionamento = self.get_object()
        serializer = ConfirmarPagamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pagamento = self._registrar_pagamento(estacionamento, serializer.validated_data)

        return Response(
            {
                'estacionamento': self.get_serializer(estacionamento).data,
                'pagamento': PagamentoSerializer(pagamento).data,
            }
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def renovar(self, request, pk=None):
        estacionamento = self.get_object()

        if estacionamento.status != Estacionamento.ATIVO:
            return Response(
                {'detail': 'Somente estacionamentos ativos podem ser renovados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RenovarEstacionamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pagamento = self._registrar_pagamento(estacionamento, serializer.validated_data)

        return Response(
            {
                'estacionamento': self.get_serializer(estacionamento).data,
                'pagamento': PagamentoSerializer(pagamento).data,
            }
        )

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def encerrar(self, request, pk=None):
        estacionamento = self.get_object()

        if estacionamento.status != Estacionamento.ATIVO:
            return Response(
                {'detail': 'Este estacionamento ja foi encerrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estacionamento.status = Estacionamento.ENCERRADO
        estacionamento.hora_fim = timezone.now()
        estacionamento.save(update_fields=['status', 'hora_fim', 'atualizado_em'])

        vaga = estacionamento.vaga
        vaga.status = Vaga.LIVRE
        vaga.save(update_fields=['status', 'atualizada_em'])

        return Response(self.get_serializer(estacionamento).data)

    def _registrar_pagamento(self, estacionamento, validated_data):
        agora = timezone.now()
        tempo_minutos = validated_data['tempo_minutos']
        if estacionamento.hora_fim and estacionamento.hora_fim > agora:
            base = estacionamento.hora_fim
        else:
            base = agora

        estacionamento.hora_fim = base + timedelta(minutes=tempo_minutos)
        estacionamento.status = Estacionamento.ATIVO
        estacionamento.vaga.status = Vaga.OCUPADA
        estacionamento.vaga.save(update_fields=['status', 'atualizada_em'])
        estacionamento.save(update_fields=['hora_fim', 'status', 'atualizado_em'])

        pagamento = Pagamento.objects.create(
            estacionamento=estacionamento,
            valor=validated_data['valor'],
            tempo_comprado=tempo_minutos,
            forma_pagamento=validated_data['forma_pagamento'],
            data_pagamento=agora,
        )

        usuario = estacionamento.veiculo.usuario
        usuario.pontos += 1
        usuario.save(update_fields=['pontos'])

        return pagamento


class PagamentoViewSet(viewsets.ModelViewSet):
    queryset = Pagamento.objects.select_related(
        'estacionamento',
        'estacionamento__veiculo',
        'estacionamento__vaga',
    ).all()
    serializer_class = PagamentoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        estacionamento_id = self.request.query_params.get('estacionamento')
        usuario_id = self.request.query_params.get('usuario')

        if estacionamento_id:
            queryset = queryset.filter(estacionamento_id=estacionamento_id)
        if usuario_id:
            queryset = queryset.filter(estacionamento__veiculo__usuario_id=usuario_id)

        return queryset


class FiscalViewSet(viewsets.ModelViewSet):
    queryset = Fiscal.objects.all()
    serializer_class = FiscalSerializer


class MultaViewSet(viewsets.ModelViewSet):
    queryset = Multa.objects.select_related(
        'estacionamento',
        'estacionamento__veiculo',
        'estacionamento__vaga',
        'fiscal',
    ).all()
    serializer_class = MultaSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        fiscal_id = self.request.query_params.get('fiscal')
        usuario_id = self.request.query_params.get('usuario')

        if status_param:
            queryset = queryset.filter(status=status_param)
        if fiscal_id:
            queryset = queryset.filter(fiscal_id=fiscal_id)
        if usuario_id:
            queryset = queryset.filter(estacionamento__veiculo__usuario_id=usuario_id)

        return queryset
