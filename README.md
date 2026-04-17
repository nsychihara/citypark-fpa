# CityPark API

API REST em Django para o aplicativo CityPark, um sistema de gerenciamento de estacionamento urbano. O projeto foi estruturado a partir do fluxo visual do prototipo mobile e do modelo SQL da aplicacao.

## Funcionalidades

- Cadastro e login de usuarios.
- Cadastro de veiculos por usuario.
- Cadastro e consulta de vagas por rua, regiao e status.
- Listagem de vagas disponiveis.
- Inicio de estacionamento.
- Confirmacao de pagamento.
- Renovacao de tempo.
- Encerramento de estacionamento.
- Historico de estacionamentos e pagamentos.
- Controle de pontos do usuario.
- Cadastro de fiscais e multas.

## Tecnologias

- Python 3
- Django 6
- Django REST Framework
- SQLite para desenvolvimento local
- MySQL suportado pelas dependencias do ambiente

## Estrutura

```text
citypark/
├── app/
│   ├── admin.py          # Configuracao do Django Admin
│   ├── models.py         # Modelos principais da API
│   ├── serializers.py    # Serializacao e validacoes da API
│   ├── tests.py          # Testes automatizados
│   ├── urls.py           # Rotas da aplicacao
│   └── views.py          # ViewSets e acoes do fluxo CityPark
├── citypark/
│   ├── settings.py       # Configuracoes do projeto Django
│   └── urls.py           # Rotas globais do projeto
├── db.sqlite3            # Banco local de desenvolvimento
└── manage.py
```

## Modelos Principais

### Usuario

Representa a pessoa que usa o app.

Campos principais:

- `nome`
- `email`
- `senha`
- `pontos`
- `criado_em`

### Veiculo

Representa o carro cadastrado pelo usuario.

Campos principais:

- `placa`
- `modelo`
- `cor`
- `usuario`

### Vaga

Representa uma vaga de estacionamento exibida no mapa/listagem.

Campos principais:

- `numero`
- `rua`
- `regiao`
- `descricao`
- `latitude`
- `longitude`
- `preco_hora`
- `status`

Status possiveis:

- `livre`
- `ocupada`
- `manutencao`

### Estacionamento

Representa uma sessao de estacionamento ativa ou encerrada.

Campos principais:

- `veiculo`
- `vaga`
- `hora_inicio`
- `hora_fim`
- `status`

Status possiveis:

- `ativo`
- `encerrado`
- `expirado`

### Pagamento

Representa um pagamento ou renovacao de tempo.

Campos principais:

- `estacionamento`
- `valor`
- `tempo_comprado`
- `forma_pagamento`
- `data_pagamento`

Formas de pagamento:

- `pix`
- `debito`
- `credito`
- `pontos`

### Fiscal e Multa

Modelos usados para fiscalizacao de estacionamentos irregulares.

## Como Rodar

Use o ambiente virtual existente do projeto:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

A API ficara disponivel em:

```text
http://127.0.0.1:8000/api/
```

O painel administrativo fica em:

```text
http://127.0.0.1:8000/admin/
```

## Comandos Uteis

Rodar verificacao do Django:

```bash
.venv/bin/python manage.py check
```

Rodar testes:

```bash
.venv/bin/python manage.py test
```

Criar novas migrations depois de alterar modelos:

```bash
.venv/bin/python manage.py makemigrations
```

Aplicar migrations:

```bash
.venv/bin/python manage.py migrate
```

Criar usuario administrador:

```bash
.venv/bin/python manage.py createsuperuser
```

## Endpoints

Todas as rotas ficam abaixo de `/api/`.

### Usuarios

```http
GET    /api/usuarios/
POST   /api/usuarios/
GET    /api/usuarios/{id}/
PUT    /api/usuarios/{id}/
PATCH  /api/usuarios/{id}/
DELETE /api/usuarios/{id}/
POST   /api/usuarios/login/
```

Exemplo de cadastro:

```json
{
  "nome": "Gustavo",
  "email": "gustavo@example.com",
  "senha": "123456"
}
```

Exemplo de login:

```json
{
  "email": "gustavo@example.com",
  "senha": "123456"
}
```

A resposta de login retorna o usuario e, se existir, o estacionamento ativo.

### Veiculos

```http
GET    /api/veiculos/
POST   /api/veiculos/
GET    /api/veiculos/{id}/
PUT    /api/veiculos/{id}/
PATCH  /api/veiculos/{id}/
DELETE /api/veiculos/{id}/
```

Filtro por usuario:

```http
GET /api/veiculos/?usuario=1
```

Exemplo:

```json
{
  "placa": "ABC-1234",
  "modelo": "Cruze 2024",
  "cor": "azul",
  "usuario": 1
}
```

### Vagas

```http
GET    /api/vagas/
POST   /api/vagas/
GET    /api/vagas/{id}/
PUT    /api/vagas/{id}/
PATCH  /api/vagas/{id}/
DELETE /api/vagas/{id}/
GET    /api/vagas/disponiveis/
GET    /api/vagas/resumo/
```

Filtros:

```http
GET /api/vagas/?status=livre
GET /api/vagas/?regiao=regiao A
GET /api/vagas/?rua=Sampaio
```

Exemplo:

```json
{
  "numero": "16",
  "rua": "Sampaio Vidal",
  "regiao": "regiao A",
  "descricao": "Rua plana, altamente movimentada",
  "latitude": "-22.21750000",
  "longitude": "-49.95000000",
  "preco_hora": "8.00",
  "status": "livre"
}
```

### Estacionamentos

```http
GET    /api/estacionamentos/
POST   /api/estacionamentos/
GET    /api/estacionamentos/{id}/
PUT    /api/estacionamentos/{id}/
PATCH  /api/estacionamentos/{id}/
DELETE /api/estacionamentos/{id}/
GET    /api/estacionamentos/ativo/
POST   /api/estacionamentos/iniciar/
POST   /api/estacionamentos/{id}/confirmar_pagamento/
POST   /api/estacionamentos/{id}/renovar/
POST   /api/estacionamentos/{id}/encerrar/
```

Filtros:

```http
GET /api/estacionamentos/?usuario=1
GET /api/estacionamentos/?veiculo=1
GET /api/estacionamentos/?status=ativo
```

Iniciar estacionamento:

```json
{
  "veiculo": 1,
  "vaga": 1,
  "tempo_minutos": 60,
  "valor": "8.00",
  "forma_pagamento": "pix"
}
```

Renovar estacionamento:

```json
{
  "tempo_minutos": 30,
  "valor": "4.00",
  "forma_pagamento": "credito"
}
```

Encerrar estacionamento:

```http
POST /api/estacionamentos/1/encerrar/
```

### Pagamentos

```http
GET    /api/pagamentos/
POST   /api/pagamentos/
GET    /api/pagamentos/{id}/
PUT    /api/pagamentos/{id}/
PATCH  /api/pagamentos/{id}/
DELETE /api/pagamentos/{id}/
```

Filtros:

```http
GET /api/pagamentos/?estacionamento=1
GET /api/pagamentos/?usuario=1
```

### Fiscais

```http
GET    /api/fiscais/
POST   /api/fiscais/
GET    /api/fiscais/{id}/
PUT    /api/fiscais/{id}/
PATCH  /api/fiscais/{id}/
DELETE /api/fiscais/{id}/
```

### Multas

```http
GET    /api/multas/
POST   /api/multas/
GET    /api/multas/{id}/
PUT    /api/multas/{id}/
PATCH  /api/multas/{id}/
DELETE /api/multas/{id}/
```

Filtros:

```http
GET /api/multas/?status=pendente
GET /api/multas/?fiscal=1
GET /api/multas/?usuario=1
```

## Fluxo Principal do App

1. Criar usuario em `POST /api/usuarios/`.
2. Fazer login em `POST /api/usuarios/login/`.
3. Cadastrar veiculo em `POST /api/veiculos/`.
4. Consultar vagas livres em `GET /api/vagas/disponiveis/`.
5. Iniciar estacionamento em `POST /api/estacionamentos/iniciar/`.
6. Renovar tempo em `POST /api/estacionamentos/{id}/renovar/`.
7. Encerrar estacionamento em `POST /api/estacionamentos/{id}/encerrar/`.
8. Consultar historico em `GET /api/estacionamentos/?usuario={id}`.

## Observacoes

- A API usa um login simples para o prototipo. Ela ainda nao usa JWT ou autenticacao por token.
- Senhas criadas pela API sao salvas com hash.
- O login aceita senha legada em texto puro para compatibilidade com dados antigos.
- Ao iniciar um estacionamento, a vaga passa para `ocupada`.
- Ao encerrar um estacionamento, a vaga volta para `livre`.
- Ao confirmar pagamento ou renovar tempo, o usuario recebe ponto de contribuicao.

## Testes

Existe um teste automatizado cobrindo o fluxo principal:

- login
- inicio de estacionamento
- ocupacao da vaga
- renovacao de tempo
- encerramento
- liberacao da vaga

Execute com:

```bash
.venv/bin/python manage.py test
```
