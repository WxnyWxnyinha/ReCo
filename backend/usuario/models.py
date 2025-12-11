from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('doador', 'Doador'),
        ('beneficiario', 'Beneficiário'),
        ('pj', 'Empresa/ONG'),
        ('transportador', 'Transportador/Voluntário'),
        ('reciclador', 'Parceiro Reciclador'),
        ('admin', 'Administrador'),
    )

    CITY_CHOICES = (
        ('plano_piloto', 'Plano Piloto (RA I)'),
        ('gama', 'Gama (RA II)'),
        ('taguatinga', 'Taguatinga (RA III)'),
        ('brazlandia', 'Brazlândia (RA IV)'),
        ('sobradinho', 'Sobradinho (RA V)'),
        ('planaltina', 'Planaltina (RA VI)'),
        ('paranoa', 'Paranoá (RA VII)'),
        ('nucleo_bandeirante', 'Núcleo Bandeirante (RA VIII)'),
        ('ceilandia', 'Ceilândia (RA IX)'),
        ('guara', 'Guará (RA X)'),
        ('cruzeiro', 'Cruzeiro (RA XI)'),
        ('samambaia', 'Samambaia (RA XII)'),
        ('santa_maria', 'Santa Maria (RA XIII)'),
        ('sao_sebastiao', 'São Sebastião (RA XIV)'),
        ('recanto_das_emas', 'Recanto das Emas (RA XV)'),
        ('lago_sul', 'Lago Sul (RA XVI)'),
        ('riacho_fundo', 'Riacho Fundo (RA XVII)'),
        ('lago_norte', 'Lago Norte (RA XVIII)'),
        ('candangolandia', 'Candangolândia (RA XIX)'),
        ('aguas_claras', 'Águas Claras (RA XX)'),
        ('riacho_fundo_ii', 'Riacho Fundo II (RA XXI)'),
        ('sudoeste_octogonal', 'Sudoeste/Octogonal (RA XXII)'),
        ('varjao', 'Varjão (RA XXIII)'),
        ('park_way', 'Park Way (RA XXIV)'),
        ('scia', 'SCIA (Setor de Cidades e Indústrias Autárquicas) (RA XXV)'),
        ('sobradinho_ii', 'Sobradinho II (RA XXVI)'),
        ('jardim_botanico', 'Jardim Botânico (RA XXVII)'),
        ('itapoa', 'Itapoã (RA XXVIII)'),
        ('sia', 'SIA (Setor de Indústrias e Abastecimento) (RA XXIX)'),
        ('vicente_pires', 'Vicente Pires (RA XXX)'),
        ('fercal', 'Fercal (RA XXXI)'),
        ('sol_nascente_por_do_sol', 'Sol Nascente e Pôr do Sol (RA XXXII)'),
        ('arniqueira', 'Arniqueira (RA XXXIII)'),
        ('arapoanga', 'Arapoanga (RA XXXIV)'),
        ('agua_quente', 'Água Quente (RA XXXV)'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Telefone", max_length=20, blank=True)
    city = models.CharField("Cidade", max_length=100, choices=CITY_CHOICES, blank=True)
    user_type = models.CharField("Tipo de usuário", max_length=20, choices=USER_TYPE_CHOICES, default='doador')
    cpf_cnpj = models.CharField("CPF/CNPJ", max_length=30, blank=True)
    razao_social = models.CharField("Razão social", max_length=255, blank=True)
    birth_date = models.DateField("Data de nascimento", null=True, blank=True)
    profile_photo = models.ImageField("Foto do perfil", upload_to='profiles/', blank=True, null=True)
    
    # Campos específicos para Transportador
    is_available = models.BooleanField("Disponível para coletas", default=False)
    vehicle_type = models.CharField("Tipo de veículo", max_length=100, blank=True)
    max_items_capacity = models.IntegerField("Capacidade máxima de itens", default=0)
    
    # Campos específicos para Reciclador
    company_name = models.CharField("Nome da empresa", max_length=255, blank=True)
    certifications = models.TextField("Certificações de reciclagem", blank=True)
    
    # Campos de auditoria
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    consent_privacy = models.BooleanField("Consentimento LGPD", default=False)
    consent_timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()