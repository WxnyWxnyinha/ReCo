from django.db import models
from django.conf import settings

class Donation(models.Model):
    CONDITION_CHOICES = [
        ('novo', 'Novo'),
        ('bom', 'Em bom estado'),
        ('ruim', 'Precisa de reparo'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('em_rota', 'Em Rota'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
        ('reciclagem', 'Para Reciclagem'),
    ]
    
    DELIVERY_TYPE_CHOICES = [
        ('coleta', 'Ponto de Coleta'),
        ('domicilio', 'Retirada em Domicílio'),
    ]

    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='bom')
    city = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True, help_text="Email de contato (opcional)")
    contact_phone = models.CharField(max_length=30, blank=True)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donations')
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='donations/', blank=True, null=True)
    
    # Novos campos
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_donations')
    approved_at = models.DateTimeField(null=True, blank=True)
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_TYPE_CHOICES, default='coleta')
    collection_point = models.ForeignKey('CollectionPoint', on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    beneficiary = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_donations', help_text="Beneficiário que vai receber a doação")
    
    # Endereço para retirada em domicílio
    pickup_address = models.CharField("Endereço para retirada", max_length=300, blank=True)
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.get_status_display()}"


class DonationRequest(models.Model):
    """Modelo para solicitação de uma doação por um beneficiário"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('rejeitada', 'Rejeitada'),
        ('entregue', 'Entregue'),
    ]
    
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='requests')
    beneficiary = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donation_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    reason = models.TextField("Motivo da solicitação")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    rejection_reason = models.TextField("Motivo da rejeição", blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('donation', 'beneficiary')  # Uma solicitação por beneficiário por doação

    def __str__(self):
        return f"{self.beneficiary.username} solicitou {self.donation.title} - {self.get_status_display()}"


class CollectionPoint(models.Model):
    """Modelo para pontos de coleta físicos"""
    name = models.CharField("Nome do ponto", max_length=200)
    address = models.CharField("Endereço", max_length=300)
    latitude = models.FloatField()
    longitude = models.FloatField()
    opening_hours = models.CharField("Horário de funcionamento", max_length=100, help_text="ex: 08:00-17:00")
    capacity = models.IntegerField("Capacidade em itens", default=50)
    is_active = models.BooleanField(default=True)
    phone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='collection_points_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.address}"
    
    def current_inventory(self):
        """Retorna quantidade atual de itens"""
        return self.donations.filter(status__in=['aprovada', 'em_rota']).count()


class Message(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    text = models.TextField()
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Msg from {self.sender} to {self.recipient} on {self.donation}'


class Delivery(models.Model):
    """Modelo para rastreamento de entregas"""
    STATUS_CHOICES = [
        ('atribuida', 'Atribuída'),
        ('coletada', 'Coletada'),
        ('em_transito', 'Em Trânsito'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
    ]
    
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='delivery')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='atribuida')
    
    # Informações de coleta
    assigned_at = models.DateTimeField(auto_now_add=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    
    # Informações de entrega
    delivered_at = models.DateTimeField(null=True, blank=True)
    proof_image = models.ImageField("Comprovante com foto", upload_to='deliveries/', blank=True, null=True)
    signature_image = models.ImageField("Assinatura digital", upload_to='deliveries/', blank=True, null=True)
    
    # Geolocalização
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    delivery_latitude = models.FloatField(null=True, blank=True)
    delivery_longitude = models.FloatField(null=True, blank=True)
    
    # Notas
    notes = models.TextField("Observações", blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Entrega #{self.pk} - {self.donation.title} - {self.get_status_display()}"
    
    def is_pending(self):
        return self.status in ['atribuida', 'coletada', 'em_transito']
    
    def is_completed(self):
        return self.status in ['entregue', 'cancelada']


class RecyclingPartner(models.Model):
    """Modelo para parceiros de reciclagem"""
    company_name = models.CharField("Nome da empresa", max_length=200)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    address = models.CharField("Endereço", max_length=300)
    phone = models.CharField("Telefone", max_length=20)
    email = models.EmailField("Email de contato")
    
    # Certificações
    environmental_license = models.CharField("Licença ambiental", max_length=100, blank=True)
    certifications = models.TextField("Certificações", blank=True, help_text="ISO, etc.")
    
    # Capacidade de processamento
    accepts_electronics = models.BooleanField("Aceita eletrônicos", default=True)
    accepts_batteries = models.BooleanField("Aceita baterias", default=True)
    accepts_metals = models.BooleanField("Aceita metais", default=True)
    max_monthly_capacity_kg = models.IntegerField("Capacidade mensal (kg)", default=1000)
    
    # Status
    is_active = models.BooleanField(default=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    # Responsável
    contact_person = models.CharField("Pessoa de contato", max_length=100)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']
        verbose_name = "Parceiro de Reciclagem"
        verbose_name_plural = "Parceiros de Reciclagem"

    def __str__(self):
        return f"{self.company_name} ({self.cnpj})"


class RecyclingBatch(models.Model):
    """Modelo para lotes de reciclagem de itens não reutilizáveis"""
    STATUS_CHOICES = [
        ('criado', 'Criado'),
        ('coletado', 'Coletado'),
        ('enviado', 'Enviado ao reciclador'),
        ('processado', 'Processado'),
        ('certificado', 'Certificado'),
    ]
    
    # Identificação do lote
    batch_code = models.CharField("Código do lote", max_length=50, unique=True)
    partner = models.ForeignKey(RecyclingPartner, on_delete=models.PROTECT, related_name='batches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='criado')
    
    # Itens do lote
    items = models.ManyToManyField(Donation, related_name='recycling_batches', blank=True)
    
    # Peso e processamento
    estimated_weight_kg = models.FloatField("Peso estimado (kg)", default=0)
    actual_weight_kg = models.FloatField("Peso real (kg)", null=True, blank=True)
    
    # Datas do processo
    created_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField("Data de coleta", null=True, blank=True)
    sent_at = models.DateTimeField("Data de envio", null=True, blank=True)
    processed_at = models.DateTimeField("Data de processamento", null=True, blank=True)
    
    # Certificação
    certificate_number = models.CharField("Número do certificado", max_length=100, blank=True)
    certificate_file = models.FileField("Arquivo do certificado", upload_to='recycling_certificates/', blank=True, null=True)
    certificate_issued_at = models.DateTimeField("Data de emissão do certificado", null=True, blank=True)
    
    # Responsáveis
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recycling_batches_created')
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='recycling_batches_processed')
    
    # Notas
    notes = models.TextField("Observações", blank=True)
    
    # Metadata
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lote de Reciclagem"
        verbose_name_plural = "Lotes de Reciclagem"

    def __str__(self):
        return f"Lote {self.batch_code} - {self.get_status_display()}"
    
    def total_items(self):
        """Retorna total de itens no lote"""
        return self.items.count()
    
    def update_estimated_weight(self):
        """Atualiza peso estimado baseado no número de itens (3kg por item)"""
        self.estimated_weight_kg = self.total_items() * 3
        self.save()
    
    def calculate_environmental_impact(self):
        """Calcula impacto ambiental do lote"""
        weight = self.actual_weight_kg or self.estimated_weight_kg
        return {
            'co2_avoided_kg': weight * 60,
            'energy_saved_kwh': weight * 15,
            'water_saved_liters': weight * 500,
            'trees_preserved': weight * 0.05,
        }