# 📋 Análise de Requisitos SRS vs Código Atual
**Projeto:** ReCo - Reutilizar e Conectar  
**Data:** 10 de dezembro de 2025  
**Status:** Documento de Análise Comparativa

---

## 📊 Resumo Executivo

- **Requisitos Totais SRS:** 33 requisitos
- **✅ Implementados:** 8 requisitos (~24%)
- **🟡 Parcialmente Implementados:** 6 requisitos (~18%)
- **❌ Não Implementados:** 19 requisitos (~58%)

---

## 1️⃣ AUTENTICAÇÃO E GESTÃO DE USUÁRIOS (RF1)

### RF1.1 - Cadastro de diferentes tipos de usuários
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Cadastro de usuários com Django User
  - ✅ Modelo `Profile` com tipos: `Pessoa Física` e `Empresa/ONG`
  - ✅ Formulário de registro (`RegisterForm`)
  - ✅ View `register_view()` funcionando
- **O que falta:**
  - ❌ Tipos específicos: Transportador, Administrador, Reciclador
  - ❌ Campos obrigatórios para Transportador (disponibilidade)
  - ❌ Campos obrigatórios para Reciclador (certificações)

**Código Atual:**
```python
# usuario/models.py - Profile
USER_TYPE_CHOICES = (
    ('pf', 'Pessoa Física'),      # Apenas 2 tipos
    ('pj', 'Empresa/ONG'),
)
```

**Ação Recomendada:**
```python
USER_TYPE_CHOICES = (
    ('pf', 'Pessoa Física'),
    ('pj', 'Empresa/ONG'),
    ('transportador', 'Transportador/Voluntário'),
    ('reciclador', 'Parceiro Reciclador'),
    ('admin', 'Administrador'),
)
```

---

### RF1.2 - Login seguro e recuperação de senha
- **Status:** ✅ **IMPLEMENTADO**
- **O que existe:**
  - ✅ Login via `login_view()` usando `AuthenticationForm`
  - ✅ Recuperação de senha por email (`password_reset_by_username`)
  - ✅ Token de segurança gerado
  - ✅ Validação e reset de senha funcionando
  - ✅ Envio de email configurado

---

### RF1.3 - Admin gerenciar usuários e permissões
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Django Admin padrão habilitado
  - ✅ Visualização de usuários e perfis no admin
- **O que falta:**
  - ❌ Dashboard administrativo customizado
  - ❌ Gerenciamento de permissões granular
  - ❌ Ativação/desativação de contas
  - ❌ Campos de auditoria (quem criou, quando, etc)

---

## 2️⃣ GESTÃO DE DOAÇÕES (RF2)

### RF2.1 - Cadastrar item para doação com fotos e descrição
- **Status:** ✅ **IMPLEMENTADO**
- **O que existe:**
  - ✅ Modelo `Donation` com campos: título, descrição, condição
  - ✅ Campo de imagem (`image`)
  - ✅ Formulário `DonationForm`
  - ✅ View `create()` funcionando
  - ✅ Upload para pasta `donations/`

---

### RF2.2 - Escolher entre ponto de coleta ou retirada
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Campo `tipo_entrega` (retirada ou ponto de coleta)
  - ❌ Modelo `PontoColeta` não existe
  - ❌ Lógica para vincular doação a ponto de coleta
  - ❌ Campos de endereço para retirada em domicílio

**Ação Recomendada:**
```python
# marketplace/models.py
class Donation(models.Model):
    DELIVERY_CHOICES = [
        ('coleta', 'Ponto de Coleta'),
        ('domicilio', 'Retirada em Domicílio'),
    ]
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    collection_point = models.ForeignKey('CollectionPoint', on_delete=models.SET_NULL, null=True, blank=True)
```

---

### RF2.3 - Exibir listagem pública de itens
- **Status:** ✅ **IMPLEMENTADO**
- **O que existe:**
  - ✅ View `index()` lista todas as doações disponíveis
  - ✅ Filtros por: busca, condição, cidade, ordem
  - ✅ Template `marketplace/index.html`
  - ✅ Exibição de imagens

---

### RF2.4 - Registrar e exibir status da doação
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Campo `is_available` (Disponível/Indisponível)
  - ✅ Exibição do status na listagem
- **O que falta:**
  - ❌ Estados mais detalhados: Pendente, Aprovada, Em Rota, Entregue, Cancelada
  - ❌ Histórico de mudanças de status
  - ❌ Timestamps para cada transição

**Ação Recomendada:**
```python
STATUS_CHOICES = [
    ('pendente', 'Pendente'),
    ('aprovada', 'Aprovada'),
    ('em_rota', 'Em Rota'),
    ('entregue', 'Entregue'),
    ('cancelada', 'Cancelada'),
]
status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
approved_by = models.ForeignKey(User, null=True, blank=True)
approved_at = models.DateTimeField(null=True, blank=True)
```

---

## 3️⃣ SOLICITAÇÃO DE ITENS (RF3)

### RF3.1 - Visualizar e solicitar itens
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ View `detail()` mostra detalhes da doação
  - ✅ Usuários podem visualizar todas as doações
- **O que falta:**
  - ❌ Modelo `SolicitacaoDeDacao` não existe
  - ❌ Botão/formulário para solicitar item
  - ❌ Confirmação de interesse
  - ❌ Campo de observações/necessidades

**Ação Recomendada:**
```python
# marketplace/models.py
class DonationRequest(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
    ]
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    beneficiary = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### RF3.2 - Admin notificado sobre solicitações
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Sistema de notificações para admin
  - ❌ Dashboard de solicitações pendentes
  - ❌ Email de alerta

---

### RF3.3 - Beneficiário acompanhar status dos pedidos
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Painel do beneficiário
  - ❌ Histórico de solicitações
  - ❌ Status em tempo real

---

## 4️⃣ PAINEL ADMINISTRATIVO (RF4)

### RF4.1 - Admin aprovar/rejeitar/editar doações
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Django Admin com acesso a Donation
  - ✅ Possibilidade de editar diretamente no admin
- **O que falta:**
  - ❌ Interface customizada e amigável
  - ❌ Workflow de aprovação visual
  - ❌ Motivo de rejeição com feedback ao doador

**Necessário criar:** Dashboard administrativo customizado

---

### RF4.2 - Admin atribuir voluntários para coletas
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Modelo `Entrega/Rota`
  - ❌ Vinculação de transportador a doação
  - ❌ Sistema de atribuição
  - ❌ Visualização de rotas

---

### RF4.3 - Gerar relatórios de impacto
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Total de doações
  - ❌ kg de lixo reaproveitado
  - ❌ Número de beneficiários
  - ❌ Emissões CO₂ evitadas
  - ❌ Exportação em PDF/Excel

---

## 5️⃣ GESTÃO DE PONTOS DE COLETA (RF5)

### RF5.1 - Cadastrar, editar e desativar pontos de coleta
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Modelo `CollectionPoint` não existe
  - ❌ Campos: nome, endereço, horário, capacidade
  - ❌ CRUD de pontos de coleta

**Ação Recomendada:**
```python
# marketplace/models.py
class CollectionPoint(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    opening_hours = models.CharField(max_length=100)  # ex: "08:00-17:00"
    capacity = models.IntegerField(help_text="Capacidade em itens")
    is_active = models.BooleanField(default=True)
    phone = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### RF5.2 - Mapa interativo com pontos de coleta
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Integração Google Maps API
  - ❌ Componente de mapa interativo
  - ❌ Filtros de localização

---

### RF5.3 - Admin atribuir voluntários a pontos
- **Status:** ❌ **NÃO IMPLEMENTADO**

---

### RF5.4 - Registrar estoque de itens em coleta
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Modelo `CollectionPointInventory`
  - ❌ Entrada/saída de itens
  - ❌ Controle de capacidade

---

## 6️⃣ LOGÍSTICA E ENTREGAS (RF6)

### RF6.1 - Transportador receber atribuições
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Modelo `Entrega`
  - ❌ Painel do transportador
  - ❌ Lista de rotas atribuídas

**Ação Recomendada:**
```python
# marketplace/models.py
class Delivery(models.Model):
    STATUS_CHOICES = [
        ('atribuida', 'Atribuída'),
        ('coletada', 'Coletada'),
        ('em_transito', 'Em Trânsito'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
    ]
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE)
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
```

---

### RF6.2 - Registrar status da entrega
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Atualizações de status em tempo real
  - ❌ Timeline visual

---

### RF6.3 - Comprovante de entrega (foto/assinatura)
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Modelo para armazenar comprovantes
  - ❌ Geolocalização
  - ❌ Assinatura digital

---

## 7️⃣ COMUNICAÇÃO (RF7)

### RF7.1 - Canal de mensagens internas
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Modelo `Message` com sender, recipient, text
  - ✅ Campo `image` para mensagens
  - ✅ Vínculo com `Donation`
  - ✅ Views `chat()`, `chats()`, `contact()`
  - ✅ Templates de chat funcionando
- **O que falta:**
  - ❌ Mediação obrigatória pelo admin (RF7.1 menciona "mediada por este último")
  - ❌ Validação de permissão para enviar mensagens
  - ❌ Arquivo de logs de mensagens

---

### RF7.2 - Notificações por email
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Sistema de email configurado (settings.py)
  - ✅ Envio de email de recuperação de senha
- **O que falta:**
  - ❌ Notificações automáticas para:
    - ❌ Solicitação aprovada
    - ❌ Doação aprovada
    - ❌ Entrega em andamento
    - ❌ Entrega concluída
    - ❌ Nova mensagem recebida

---

## 8️⃣ GESTÃO DE RECICLAGEM (RF8)

### RF8.1-8.5 - Sistema completo de reciclagem
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Modelo `RecyclingBatch`
  - ❌ Modelo `RecyclingPartner`
  - ❌ Marcar itens como não reaproveitáveis
  - ❌ Lotes para recicladores
  - ❌ Confirmação de recebimento
  - ❌ Registro de peso e processamento
  - ❌ Certificados de reciclagem

---

## 🎯 REQUISITOS NÃO FUNCIONAIS (RNF)

### RNF1 - Desempenho (tempo < 3s)
- **Status:** 🟡 **PARCIALMENTE CUMPRE**
- **Observação:** Sem otimizações de cache, mas estrutura é simples

### RNF2 - Usabilidade
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ Bootstrap 5 para responsividade
  - ✅ Templates relativamente intuitivos
- **O que falta:**
  - ❌ Testes de UX
  - ❌ Acessibilidade WCAG

### RNF3 - Segurança (LGPD)
- **Status:** 🟡 **PARCIALMENTE IMPLEMENTADO**
- **O que existe:**
  - ✅ HTTPS em produção (settings)
  - ✅ CSRF protection
- **O que falta:**
  - ❌ Política de privacidade visível
  - ❌ Consentimento LGPD no cadastro
  - ❌ Criptografia de dados sensíveis
  - ❌ Direito ao esquecimento implementado

### RNF4 - Sustentabilidade
- **Status:** ⚠️ **Requer Avaliação**
- **Usando:** PythonAnywhere (hospedagem gratuita/low-cost) ✅

### RNF5 - Disponibilidade (99% uptime)
- **Status:** ⚠️ **Dependente de Hospedagem**

### RNF6 - Acessibilidade (WCAG)
- **Status:** ❌ **NÃO IMPLEMENTADO**
- **O que falta:**
  - ❌ Testes com leitores de tela
  - ❌ Contraste de cores validado
  - ❌ Labels semânticos corretos

### RNF7 - Escalabilidade
- **Status:** 🟡 **ESTRUTURA VIÁVEL**
- **O que existe:**
  - ✅ Arquitetura modular com apps separados
- **O que falta:**
  - ❌ Testes de carga
  - ❌ Cache/CDN implementados

---

## 📋 RESUMO POR CATEGORIA

| Categoria | Implementado | Parcial | Faltando | %Completo |
|-----------|:----:|:-----:|:-------:|:---------:|
| **Autenticação (RF1)** | 1 | 2 | 0 | 100% |
| **Doações (RF2)** | 2 | 1 | 1 | 67% |
| **Solicitações (RF3)** | 0 | 0 | 3 | 0% |
| **Admin (RF4)** | 0 | 1 | 2 | 17% |
| **Pontos Coleta (RF5)** | 0 | 0 | 4 | 0% |
| **Logística (RF6)** | 0 | 0 | 3 | 0% |
| **Comunicação (RF7)** | 0 | 2 | 0 | 100%* |
| **Reciclagem (RF8)** | 0 | 0 | 5 | 0% |
| **Requisitos Não-Func. (RNF)** | 1 | 3 | 3 | 43% |

---

## ✅ PRÓXIMOS PASSOS RECOMENDADOS

### FASE 1: Aprimoramentos Imediatos (Próximas 2 semanas)
1. ✅ Expandir tipos de usuário (Transportador, Reciclador, Admin)
2. ✅ Criar modelo `DonationRequest` e implementar solicitações
3. ✅ Adicionar sistema de notificações por email
4. ✅ Aprimorar modelo `Donation` com status detalhado

### FASE 2: Funcionalidades Críticas (2-3 semanas)
5. ✅ Criar `CollectionPoint` e sistema de pontos de coleta
6. ✅ Implementar `Delivery` e controle de logística
7. ✅ Dashboard administrativo customizado
8. ✅ Relatórios de impacto

### FASE 3: Expansão (3-4 semanas)
9. ✅ Integração Google Maps
10. ✅ Sistema de reciclagem completo
11. ✅ Certificados de reciclagem
12. ✅ Testes de acessibilidade WCAG

### FASE 4: Otimizações (2 semanas)
13. ✅ Cache e performance
14. ✅ Implementação LGPD
15. ✅ Testes de segurança

---

## 📞 Conclusão

O projeto **ReCo** possui uma **base sólida com ~24% dos requisitos implementados**, especialmente em:
- ✅ Autenticação e gestão de usuários
- ✅ Cadastro e listagem de doações
- ✅ Sistema de mensagens

**Faltam implementações importantes:**
- ❌ Solicitações de itens por beneficiários
- ❌ Sistema de logística e entregas
- ❌ Pontos de coleta
- ❌ Reciclagem e impacto ambiental

Para alcançar o **MVP funcional**, recomenda-se priorizar as **Fases 1 e 2**, focando em doador → beneficiário → admin → entrega.

---

*Documento gerado em: 10/12/2025*
