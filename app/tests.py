from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Estacionamento, Usuario, Vaga, Veiculo


class CityParkApiTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create(
            nome='Gustavo',
            email='gustavo@example.com',
            senha='senha-legada',
        )
        self.veiculo = Veiculo.objects.create(
            usuario=self.usuario,
            placa='ABC-1234',
            modelo='Cruze 2024',
            cor='azul',
        )
        self.vaga = Vaga.objects.create(
            numero='16',
            rua='Sampaio Vidal',
            regiao='regiao A',
            descricao='Rua plana, altamente movimentada',
            latitude=Decimal('-22.21750000'),
            longitude=Decimal('-49.95000000'),
            preco_hora=Decimal('8.00'),
        )

    def test_fluxo_principal_de_estacionamento(self):
        resposta_login = self.client.post(
            reverse('usuario-login'),
            {'email': 'gustavo@example.com', 'senha': 'senha-legada'},
            format='json',
        )
        self.assertEqual(resposta_login.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_login.data['usuario']['email'], self.usuario.email)

        resposta_iniciar = self.client.post(
            reverse('estacionamento-iniciar'),
            {
                'veiculo': self.veiculo.id,
                'vaga': self.vaga.id,
                'tempo_minutos': 60,
                'valor': '8.00',
                'forma_pagamento': 'pix',
            },
            format='json',
        )
        self.assertEqual(resposta_iniciar.status_code, status.HTTP_201_CREATED)
        estacionamento_id = resposta_iniciar.data['id']

        self.vaga.refresh_from_db()
        self.assertEqual(self.vaga.status, Vaga.OCUPADA)

        resposta_renovar = self.client.post(
            reverse('estacionamento-renovar', args=[estacionamento_id]),
            {
                'tempo_minutos': 30,
                'valor': '4.00',
                'forma_pagamento': 'credito',
            },
            format='json',
        )
        self.assertEqual(resposta_renovar.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resposta_renovar.data['pagamento']['tempo_comprado'],
            30,
        )

        resposta_encerrar = self.client.post(
            reverse('estacionamento-encerrar', args=[estacionamento_id]),
            {},
            format='json',
        )
        self.assertEqual(resposta_encerrar.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta_encerrar.data['status'], Estacionamento.ENCERRADO)

        self.vaga.refresh_from_db()
        self.assertEqual(self.vaga.status, Vaga.LIVRE)
