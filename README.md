# ReCo - Projeto Organizado

## 📁 Estrutura do Projeto

```
CSS_ReCo/
├── backend/                          # 🔧 BACK-END (Django)
│   ├── ReCo/                        # Configurações principais do Django
│   │   ├── settings.py              # Configurações do projeto
│   │   ├── urls.py                  # URLs principais
│   │   ├── wsgi.py                  # WSGI configuration
│   │   └── asgi.py                  # ASGI configuration
│   ├── usuario/                     # App de Usuários
│   │   ├── models.py                # Modelos de usuário
│   │   ├── views.py                 # Views de autenticação e perfil
│   │   ├── forms.py                 # Formulários de usuário
│   │   ├── urls.py                  # URLs da app
│   │   ├── migrations/              # Migrações do banco de dados
│   │   └── templates/               # Templates da app
│   ├── marketplace/                 # App de Marketplace
│   │   ├── models.py                # Modelos de doações e mensagens
│   │   ├── views.py                 # Views do marketplace
│   │   ├── request_views.py         # Views de solicitações (NOVO)
│   │   ├── admin_views.py           # Views administrativas (NOVO)
│   │   ├── notifications.py         # Sistema de notificações email (NOVO)
│   │   ├── forms.py                 # Formulários
│   │   ├── urls.py                  # URLs da app
│   │   ├── admin.py                 # Customização Django Admin
│   │   ├── migrations/              # Migrações
│   │   └── templates/               # Templates da app
│   │       ├── marketplace/         # Templates de doações
│   │       ├── admin/               # Templates do painel admin (NOVO)
│   │       └── email/               # Templates de emails (NOVO)
│   ├── perfil/                      # App de Perfil
│   │   ├── models.py                # Modelos de perfil
│   │   ├── views.py                 # Views de perfil
│   │   ├── forms.py                 # Formulários
│   │   ├── urls.py                  # URLs da app
│   │   ├── migrations/              # Migrações
│   │   └── templates/               # Templates da app
│   ├── manage.py                    # Gerenciador do Django
│   ├── db.sqlite3                   # Banco de dados SQLite
│   └── requirements.txt             # Dependências Python (criar)
│
├── frontend/                        # 🎨 FRONT-END
│   ├── templates/                   # Templates HTML globais
│   │   ├── base.html                # Template base (navbar, footer)
│   │   ├── home.html                # Home page
│   │   └── perfil/                  # Templates de perfil
│   ├── static/                      # Arquivos estáticos
│   │   ├── css/                     # Estilos CSS
│   │   │   ├── style.css            # CSS customizado
│   │   │   └── bootstrap.min.css    # Bootstrap
│   │   └── images/                  # Imagens do projeto
│   ├── media/                       # Upload de usuários
│   │   ├── donations/               # Imagens de doações
│   │   └── profiles/                # Fotos de perfil
│   ├── package.json                 # Dependências Node.js
│   └── README.md                    # Documentação frontend
│
├── .gitignore                       # Arquivos ignorados pelo Git
├── .env                             # Variáveis de ambiente
└── README.md                        # Este arquivo

```

## 🚀 Como Rodar o Projeto

### 1. Entrar no ambiente virtual (Backend)

```bash
cd backend
# Windows
..\..\.venv\Scripts\activate
# Linux/Mac
source ../../../.venv/bin/activate
```

### 2. Rodar servidor Django

```bash
cd backend
python manage.py runserver
```

A aplicação estará em: **http://127.0.0.1:8000/**

### 3. Rodar migrações (se necessário)

```bash
cd backend
python manage.py migrate
```

## 📝 Apps Django (Backend)

| App | Responsabilidade |
|-----|-----------------|
| **usuario** | Autenticação, registro e gerenciamento de usuários |
| **marketplace** | Doações, mensagens, solicitações, entregas e chat |
| **perfil** | Edição de perfil e dados do usuário |

## 🎯 Modelos Principais

### Usuario
- **Profile** - Perfil expandido com 6 tipos (doador, beneficiario, transportador, reciclador, admin, pj)

### Marketplace
- **Donation** - Doações com status workflow (pendente → aprovada → em_rota → entregue)
- **DonationRequest** - Solicitações de beneficiários com aprovação
- **Delivery** - Entregas com rastreamento e geolocalização
- **CollectionPoint** - Pontos de coleta com capacidade e horários
- **Message** - Mensagens de chat entre usuários

## 🔐 Painel Administrativo

### Acesso
```
URL: http://127.0.0.1:8000/doacoes/admin/dashboard/
Requer: user.is_staff = True ou user.is_superuser = True
```

### Funcionalidades
- ✅ Dashboard com estatísticas em tempo real
- ✅ Gerenciamento de doações (filtros, busca, aprovação)
- ✅ Gerenciamento de solicitações (aprovar/rejeitar)
- ✅ Gerenciamento de entregas (rastreamento, atribuição)
- ✅ Pontos de coleta (listagem, ocupação)
- ✅ Cálculo de impacto ambiental (CO₂ evitado)

### URLs Administrativas
| URL | Função |
|-----|--------|
| `/doacoes/admin/dashboard/` | Dashboard principal |
| `/doacoes/admin/doacoes/` | Gerenciar doações |
| `/doacoes/admin/solicitacoes/` | Gerenciar solicitações |
| `/doacoes/admin/entregas/` | Gerenciar entregas |
| `/doacoes/admin/entregas/<id>/atribuir/` | Atribuir motorista |
| `/doacoes/admin/pontos-coleta/` | Pontos de coleta |

**📘 Veja mais:** [GUIA_ACESSO_ADMIN.md](GUIA_ACESSO_ADMIN.md)

## 📧 Sistema de Notificações

O ReCo possui sistema automatizado de emails para:
- Aprovação/rejeição de doações
- Aprovação/rejeição de solicitações
- Início de coleta
- Entrega concluída
- Notificação de novos pedidos para admins

Todos os templates estão em `marketplace/templates/email/`

## 📊 Progresso de Implementação

**Status Atual:** 60% Completo (20/33 requisitos SRS)

| Fase | Status | Descrição |
|------|--------|-----------|
| FASE 1 | ✅ 100% | Tipos de usuário, notificações, models |
| FASE 2.1 | ✅ 100% | Views de solicitações |
| FASE 2.2 | ✅ 100% | Modelo de entregas |
| FASE 2.3 | ✅ 100% | Painel administrativo |
| FASE 2.4 | 🔄 0% | Relatórios e impacto |
| FASE 3 | 🔄 0% | Sistema de reciclagem |
| FASE 4 | 🔄 0% | Otimizações finais |

**📘 Veja mais:** [PROGRESSO_IMPLEMENTACAO.md](PROGRESSO_IMPLEMENTACAO.md)

## 🎨 Frontend

- **HTML/CSS/JS** em `frontend/static/`
- **Templates Django** em `frontend/templates/`
- **Bootstrap 5.3.8** para responsividade
- **Tailwind CSS** para utilitários (opcional)

## 📦 Instalação de Dependências

### Backend (Python)
```bash
cd backend
pip install django pillow
```

### Frontend (Node.js - Opcional)
```bash
cd frontend
npm install
npm run build:css
```

## 🔒 Variáveis de Ambiente

Criar `.env` na raiz do projeto:

```
DJANGO_DEBUG=1
DJANGO_SECRET_KEY=sua-chave-secreta
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

## 📊 Banco de Dados

- **Desenvolvimento**: SQLite (`backend/db.sqlite3`)
- **Produção**: MySQL (conforme variáveis de ambiente)

## 📞 Contato

Para dúvidas, entre em contato com o time de desenvolvimento!
