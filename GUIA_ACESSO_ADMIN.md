# 🔑 GUIA DE ACESSO - Painel Administrativo ReCo

## 🎯 Pré-requisitos

Para acessar o painel administrativo, você precisa:

1. ✅ **Conta de Usuário Criada** (via `/usuario/cadastro/`)
2. ✅ **Permissões de Admin** (usuário com `is_staff=True` ou `is_superuser=True`)
3. ✅ **Servidor Django rodando** (port 8000)

---

## 🚀 Passo a Passo

### 1. Criar Superusuário (Se ainda não existe)

```bash
cd c:\Users\Wendy\Documents\ReCo\CSS_ReCo\backend
c:\Users\Wendy\Documents\ReCo\.venv\Scripts\python.exe manage.py createsuperuser
```

Preencha:
- Username: `admin`
- Email: `admin@reco.com.br`
- Password: (sua senha)

### 2. Iniciar Servidor

```bash
cd c:\Users\Wendy\Documents\ReCo\CSS_ReCo\backend
c:\Users\Wendy\Documents\ReCo\.venv\Scripts\python.exe manage.py runserver
```

### 3. Acessar o Sistema

**Opção 1: Dashboard Customizado**
```
http://127.0.0.1:8000/doacoes/admin/dashboard/
```

**Opção 2: Django Admin (Padrão)**
```
http://127.0.0.1:8000/admin/
```

### 4. Login

Use as credenciais do superusuário criado no passo 1.

---

## 📍 URLs Disponíveis

| URL | Descrição | Acesso |
|-----|-----------|--------|
| `/doacoes/admin/dashboard/` | **Dashboard Principal** - Visão geral com estatísticas | Admin |
| `/doacoes/admin/doacoes/` | Gerenciamento de Doações - Listar e filtrar | Admin |
| `/doacoes/admin/solicitacoes/` | Gerenciamento de Solicitações - Aprovar/Rejeitar | Admin |
| `/doacoes/admin/entregas/` | Gerenciamento de Entregas - Rastrear | Admin |
| `/doacoes/admin/entregas/<id>/atribuir/` | Atribuir Transportador a uma Entrega | Admin |
| `/doacoes/admin/pontos-coleta/` | Gerenciar Pontos de Coleta | Admin |
| `/admin/` | Django Admin (Interface padrão) | Superuser |

---

## 🔐 Permissões

### Como tornar um usuário Admin?

**Via Django Admin:**
```
1. Acesse: http://127.0.0.1:8000/admin/
2. Vá em "Usuários" (Users)
3. Clique no usuário desejado
4. Marque "Status de equipe" (is_staff = True)
5. Salve
```

**Via Shell:**
```bash
c:\Users\Wendy\Documents\ReCo\.venv\Scripts\python.exe manage.py shell
```
```python
from django.contrib.auth.models import User

# Tornar um usuário admin
user = User.objects.get(username='joao')
user.is_staff = True
user.save()

# Tornar superuser (todas as permissões)
user.is_superuser = True
user.save()
```

---

## 🎨 Interface do Dashboard

### O que você verá:

**1. Cabeçalho:**
- Título "Painel Administrativo"
- Botões de navegação rápida (Doações, Solicitações, Entregas)

**2. Cards de Estatísticas (4):**
- 📦 Total de Doações
- ⏳ Solicitações Pendentes
- 🚚 Entregas em Progresso
- 🌍 CO₂ Evitado

**3. Widgets de Ação Rápida:**
- 5 doações mais recentes pendentes de aprovação
- 5 solicitações mais recentes pendentes de revisão

**4. Tabela de Entregas:**
- Entregas ativas com status, transportador, horários

**5. Resumo Mensal:**
- Doações este mês
- Solicitações este mês
- Kg de resíduos reutilizados

---

## 🧪 Testar o Painel

### Cenário 1: Aprovar uma Doação Pendente

```
1. Acesse: /doacoes/admin/doacoes/
2. Filtre por Status = "Pendente"
3. Clique no ícone de olho (👁️) para ver detalhes
4. Clique no ícone de check (✓) → Vai ao Django Admin
5. Aprove alterando Status para "Aprovada"
6. Salve → Email será enviado automaticamente
```

### Cenário 2: Aprovar uma Solicitação

```
1. Acesse: /doacoes/admin/solicitacoes/
2. Filtre por Status = "Pendente"
3. Clique em "Revisar"
4. Leia o motivo da solicitação
5. Clique "Aprovar" ou "Rejeitar"
6. Beneficiário recebe email automático
```

### Cenário 3: Atribuir Entrega

```
1. Acesse: /doacoes/admin/entregas/
2. Encontre uma doação aprovada sem delivery
3. Clique em "Atribuir"
4. Selecione um transportador disponível
5. Confirme → Status muda para "Em Rota"
```

---

## ⚠️ Troubleshooting

### Erro: "Você não tem permissão"
**Solução:** Verifique se `user.is_staff = True`

### Erro: "Página não encontrada (404)"
**Solução:** Verifique se está usando o namespace correto nas URLs

### Dashboard vazio
**Solução:** Crie alguns dados de teste primeiro:
```python
# Via shell
from marketplace.models import Donation, DonationRequest
from django.contrib.auth.models import User

# Criar uma doação de teste
doador = User.objects.first()
Donation.objects.create(
    title="Monitor LG 21 polegadas",
    description="Monitor em ótimo estado",
    condition="funcionando",
    donor=doador,
    status="pendente"
)
```

### Email não está sendo enviado
**Solução:** Em desenvolvimento, emails vão para console. Verifique o terminal.

---

## 📊 Dados de Exemplo

Para testar o dashboard com dados, execute:

```bash
c:\Users\Wendy\Documents\ReCo\.venv\Scripts\python.exe manage.py shell
```

```python
from django.contrib.auth.models import User
from marketplace.models import Donation, DonationRequest, CollectionPoint, Delivery
from usuario.models import Profile

# 1. Criar usuários de teste
admin = User.objects.create_superuser('admin', 'admin@reco.com', 'admin123')
doador = User.objects.create_user('doador1', 'doador@test.com', 'pass123')
beneficiario = User.objects.create_user('beneficiario1', 'benef@test.com', 'pass123')
motorista = User.objects.create_user('motorista1', 'driver@test.com', 'pass123')

# 2. Criar perfis
Profile.objects.create(user=doador, user_type='doador')
Profile.objects.create(user=beneficiario, user_type='beneficiario')
Profile.objects.create(user=motorista, user_type='transportador', is_available=True, vehicle_type='van')

# 3. Criar doações de teste
for i in range(1, 11):
    Donation.objects.create(
        title=f"Item Eletrônico {i}",
        description=f"Descrição do item {i}",
        condition="funcionando",
        donor=doador,
        status="pendente" if i <= 5 else "aprovada"
    )

# 4. Criar solicitações
doacoes = Donation.objects.filter(status='aprovada')[:3]
for doacao in doacoes:
    DonationRequest.objects.create(
        donation=doacao,
        beneficiary=beneficiario,
        reason="Preciso deste item para minha instituição",
        status="pendente"
    )

# 5. Criar ponto de coleta
CollectionPoint.objects.create(
    name="Centro Doações Centro",
    address="Rua das Flores, 123 - Centro",
    latitude=-23.5505,
    longitude=-46.6333,
    opening_hours="Seg-Sex: 8h-18h",
    capacity=100,
    contact_person="João Silva",
    contact_phone="(11) 98765-4321"
)

print("✅ Dados de teste criados com sucesso!")
```

---

## 🎯 Checklist de Acesso

Antes de acessar, verifique:

- [ ] Servidor Django rodando (`manage.py runserver`)
- [ ] Superusuário criado (`createsuperuser`)
- [ ] Logged in com credenciais admin
- [ ] Navegador apontado para `http://127.0.0.1:8000/`
- [ ] Migrations aplicadas (`manage.py migrate`)

---

## 📱 Atalhos do Teclado (Sugeridos para futuro)

| Tecla | Ação |
|-------|------|
| `d` | Ir para Dashboard |
| `s` | Ir para Solicitações |
| `e` | Ir para Entregas |
| `p` | Ir para Pontos de Coleta |
| `/` | Focar na busca |

---

## 🎨 Customização

Para customizar o dashboard, edite:

```
marketplace/templates/admin/dashboard.html
```

Para mudar cores dos cards, modifique a seção `<style>` no final.

Para adicionar novos widgets, adicione na view `dashboard()` em:
```
marketplace/admin_views.py
```

---

## 📧 Suporte

Em caso de problemas:
1. Verifique o console do Django (terminal)
2. Verifique o console do navegador (F12)
3. Reveja os logs de erro em `/logs/` (se configurado)

---

**Status:** ✅ Pronto para uso  
**Última atualização:** 10/12/2025 às 23:45
