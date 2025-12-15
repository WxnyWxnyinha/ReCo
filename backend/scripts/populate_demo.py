import os
import sys
import django
from django.utils import timezone


def main():
    # Ensure backend project folder is on PYTHONPATH
    project_root = os.path.dirname(os.path.dirname(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ReCo.settings')
    django.setup()

    from django.contrib.auth import get_user_model
    from marketplace.models import Donation
    from marketplace.models import RecyclingPartner

    User = get_user_model()

    created = []

    # Tipos permitidos conforme Profile.USER_TYPE_CHOICES
    profils = [
        ('doador1', 'doador1@example.com', 'doador'),
        ('benef1', 'benef1@example.com', 'beneficiario'),
        ('pj1', 'pj1@example.com', 'pj'),
        ('transp1', 'transp1@example.com', 'transportador'),
        ('recic1', 'recic1@example.com', 'reciclador'),
        ('admin1', 'admin1@example.com', 'admin'),
    ]

    # Criar usuários e setar tipo no profile
    for username, email, utype in profils:
        user, created_flag = User.objects.get_or_create(username=username, defaults={'email': email})
        if created_flag:
            user.set_password('password')
            # marcar admin
            if utype == 'admin':
                user.is_staff = True
                user.is_superuser = True
            user.save()
        # Garantir que o profile exista e setar tipo
        try:
            profile = user.profile
            profile.user_type = utype
            profile.save()
        except Exception:
            # profile sinalizador pode criar automatico; ignore se não existir
            pass
        created.append(user)

    # Criar alguns doadores extras para repartir donações
    donors = []
    for i in range(1, 6):
        uname = f'doador_extra{i}'
        uemail = f'{uname}@example.com'
        u, created_flag = User.objects.get_or_create(username=uname, defaults={'email': uemail})
        if created_flag:
            u.set_password('password')
            u.save()
        try:
            u.profile.user_type = 'doador'
            u.profile.save()
        except Exception:
            pass
        # Se for transportador, marcar disponível por padrão
        try:
            if getattr(u, 'profile', None) and u.profile.user_type == 'transportador':
                u.profile.is_available = True
                u.profile.save()
        except Exception:
            pass
        donors.append(u)

    # Lista de 15 doações de lixo eletrônico
    items = [
        ('Placa-mãe de desktop', 'Placa-mãe com alguns capacitores estufados, para reciclagem.'),
        ('Monitor LCD 17"', 'Monitor com backlight danificado, display íntegro.'),
        ('Fonte ATX antiga', 'Fonte com ruídos, não testada.'),
        ('HD 500GB', 'Disco rígido usado, pode conter dados.'),
        ('Teclado mecânico', 'Teclado com algumas teclas faltando.'),
        ('Mouse óptico', 'Mouse funcional, cabo desgastado.'),
        ('Smartphone sem bateria', 'Aparelho com tela trincada e sem bateria.'),
        ('Notebook - sem bateria', 'Notebook com tela e HD, sem bateria.'),
        ('Impressora jato de tinta', 'Impressora com cabeça obstruída.'),
        ('Roteador Wi‑Fi', 'Roteador doméstico sem antenas.'),
        ('Placa de vídeo', 'Placa para peças ou reciclagem.'),
        ('Bateria Li‑ion 18650 (solta)', 'Baterias para reciclagem, manusear com cuidado.'),
        ('Carregador de notebook', 'Carregador com conector danificado.'),
        ('Teclado de notebook (peças)', 'Somente teclado, para reposição.'),
        ('Unidade óptica (DVD)', 'Drive de DVD para reciclagem ou conserto.'),
    ]

    # Criar 15 doações distribuídas entre donors
    import random

    for idx, (title, desc) in enumerate(items, start=1):
        donor = random.choice(donors)
        donation, created_flag = Donation.objects.get_or_create(
            title=title,
            donor=donor,
            defaults={
                'description': desc,
                'condition': random.choice(['ruim', 'bom', 'novo']),
                'city': 'Brasília',
                'contact_email': donor.email,
                'contact_phone': '+55 61 99999-0000',
                'is_available': True,
                'status': 'pendente',
                'delivery_type': random.choice(['coleta', 'domicilio']),
                'pickup_address': 'Setor Comercial - Brasília' if random.choice([True, False]) else '',
            }
        )
        if created_flag:
            print(f'Criada doação: {donation.title} (id={donation.pk})')

    print('População concluída.')

    # Criar parceiros de reciclagem para usuários com profile.user_type == 'reciclador'
    recicladores = []
    for user in User.objects.all():
        try:
            if getattr(user, 'profile', None) and user.profile.user_type == 'reciclador':
                recicladores.append(user)
        except Exception:
            continue

    for i, user in enumerate(recicladores, start=1):
        cnpj = f'00.000.000/0001-{i:02d}'
        partner, created_flag = RecyclingPartner.objects.get_or_create(
            company_name=f'Parceiro {user.username}',
            defaults={
                'cnpj': cnpj,
                'address': 'Endereço de exemplo',
                'phone': '+55 61 90000-0000',
                'email': user.email or f'{user.username}@example.com',
                'contact_person': user.get_full_name() or user.username,
                'is_active': True,
            }
        )
        if created_flag:
            print(f'Criado RecyclingPartner para {user.username}: {partner.company_name} (cnpj={partner.cnpj})')


if __name__ == '__main__':
    main()
