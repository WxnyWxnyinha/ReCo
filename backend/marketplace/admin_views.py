"""
Views para painel administrativo do ReCo
"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Donation, DonationRequest, Delivery, CollectionPoint
from usuario.models import Profile


def is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_staff or user.is_superuser


@user_passes_test(is_admin, login_url='usuario:login')
def dashboard(request):
    """
    Dashboard administrativo principal com estatísticas e widgets
    """
    # Período de análise (últimos 30 dias)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Estatísticas Gerais
    stats = {
        # Doações
        'total_donations': Donation.objects.count(),
        'pending_donations': Donation.objects.filter(status='pendente').count(),
        'approved_donations': Donation.objects.filter(status='aprovada').count(),
        'delivered_donations': Donation.objects.filter(status='entregue').count(),
        'donations_this_month': Donation.objects.filter(created_at__gte=thirty_days_ago).count(),
        
        # Solicitações
        'total_requests': DonationRequest.objects.count(),
        'pending_requests': DonationRequest.objects.filter(status='pendente').count(),
        'approved_requests': DonationRequest.objects.filter(status='aprovada').count(),
        'rejected_requests': DonationRequest.objects.filter(status='rejeitada').count(),
        'requests_this_month': DonationRequest.objects.filter(created_at__gte=thirty_days_ago).count(),
        
        # Entregas
        'total_deliveries': Delivery.objects.count(),
        # Contamos como pendentes apenas entregas que já foram coletadas ou estão em trânsito
        'pending_deliveries': Delivery.objects.filter(status__in=['coletada', 'em_transito']).count(),
        'delivered': Delivery.objects.filter(status='entregue').count(),
        'deliveries_this_month': Delivery.objects.filter(created_at__gte=thirty_days_ago).count(),
        
        # Usuários
        'total_donors': Profile.objects.filter(user_type='doador').count(),
        'total_beneficiaries': Profile.objects.filter(user_type='beneficiario').count(),
        'total_drivers': Profile.objects.filter(user_type='transportador', is_available=True).count(),
        'total_collection_points': CollectionPoint.objects.filter(is_active=True).count(),
    }
    
    # Cálculo de Impacto (estimativas)
    # Assumindo ~3kg por item eletrônico
    total_items = Donation.objects.filter(status__in=['aprovada', 'em_rota', 'entregue']).count()
    estimated_kg = total_items * 3
    
    # CO2 evitado: ~60kg de CO2 por kg de eletrônico reciclado
    estimated_co2_saved = estimated_kg * 60
    
    stats['estimated_kg'] = estimated_kg
    stats['estimated_co2_saved'] = estimated_co2_saved
    
    # Widgets para ações rápidas
    pending_qs = Donation.objects.filter(status='pendente').select_related('donor')[:5]
    # Anexar flags de reciclagem para uso no template
    pending_donations = []
    for pd in pending_qs:
        # usar propriedades de `Donation` para `is_recycling` e `recycling_partner_name`
        pending_donations.append(pd)
    pending_requests = DonationRequest.objects.filter(status='pendente').select_related('donation', 'beneficiary')[:5]
    # Mostrar apenas entregas efetivamente coletadas ou em trânsito — esconder atribuídas
    # Mostrar entregas que já foram coletadas, estão em trânsito ou cujo donation está 'em_rota'
    active_deliveries_qs = Delivery.objects.filter(
        Q(status__in=['coletada', 'em_transito']) | Q(donation__status='em_rota')
    ).select_related('donation', 'driver').order_by('-created_at')[:5]

    # Anexar label de exibição (mostrar 'Em Rota' quando aplicável)
    active_deliveries = []
    for ad in active_deliveries_qs:
        if getattr(ad, 'donation', None) and ad.donation.status == 'em_rota':
            ad.display_status_label = 'Em Rota'
        else:
            ad.display_status_label = ad.get_status_display()
        active_deliveries.append(ad)
    
    context = {
        'stats': stats,
        'pending_donations': pending_donations,
        'pending_requests': pending_requests,
        'active_deliveries': active_deliveries,
        'thirty_days_ago': thirty_days_ago,
    }
    
    return render(request, 'admin/dashboard.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def donations_management(request):
    """
    Gerenciamento de doações com filtros avançados
    """
    donations = Donation.objects.select_related('donor', 'approved_by', 'collection_point').order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    condition_filter = request.GET.get('condition', '')
    search = request.GET.get('search', '').strip()
    
    if status_filter:
        donations = donations.filter(status=status_filter)
    if condition_filter:
        donations = donations.filter(condition=condition_filter)
    if search:
        donations = donations.filter(Q(title__icontains=search) | Q(description__icontains=search))
    
    # Contadores
    stats = {
        'total': Donation.objects.count(),
        'pending': Donation.objects.filter(status='pendente').count(),
        'approved': Donation.objects.filter(status='aprovada').count(),
        'in_route': Donation.objects.filter(status='em_rota').count(),
        'delivered': Donation.objects.filter(status='entregue').count(),
        'canceled': Donation.objects.filter(status='cancelada').count(),
    }
    
    # Preparar lista para template: anexar atributos úteis (evitar chamadas complexas no template)
    donations_list = []
    for donation in donations:
        # usar propriedades de `Donation` no template (não sobrescrever o atributo)
        donations_list.append(donation)

    context = {
        'donations': donations_list,
        'stats': stats,
        'status_filter': status_filter,
        'condition_filter': condition_filter,
        'search': search,
        'status_choices': Donation.STATUS_CHOICES,
        'condition_choices': Donation.CONDITION_CHOICES,
    }
    
    return render(request, 'admin/donations_management.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def requests_management(request):
    """
    Gerenciamento de solicitações de doação
    """
    donation_requests = DonationRequest.objects.select_related(
        'donation', 'beneficiary', 'approved_by'
    ).order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '').strip()
    
    if status_filter:
        donation_requests = donation_requests.filter(status=status_filter)
    if search:
        donation_requests = donation_requests.filter(
            Q(beneficiary__username__icontains=search) | 
            Q(donation__title__icontains=search) |
            Q(reason__icontains=search)
        )
    
    # Contadores
    stats = {
        'total': DonationRequest.objects.count(),
        'pending': DonationRequest.objects.filter(status='pendente').count(),
        'approved': DonationRequest.objects.filter(status='aprovada').count(),
        'rejected': DonationRequest.objects.filter(status='rejeitada').count(),
        'delivered': DonationRequest.objects.filter(status='entregue').count(),
    }
    
    context = {
        'requests': donation_requests,
        'stats': stats,
        'status_filter': status_filter,
        'search': search,
        'status_choices': DonationRequest.STATUS_CHOICES,
    }
    
    return render(request, 'admin/requests_management.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def deliveries_management(request):
    """
    Gerenciamento de entregas
    """
    # Excluir entregas apenas atribuídas (aguardando coleta) para que não apareçam antes do 'pegar'
    # Incluir entregas cujo donation está em_rota (mostrar como 'Em Rota'), e também
    # outras entregas que já foram coletadas/em_transito/entregues
    deliveries = Delivery.objects.select_related('donation', 'driver').filter(
        Q(status__in=['coletada', 'em_transito', 'entregue', 'cancelada']) | Q(donation__status='em_rota')
    ).order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status', '')
    driver_filter = request.GET.get('driver', '')
    
    if status_filter:
        deliveries = deliveries.filter(status=status_filter)
    if driver_filter:
        deliveries = deliveries.filter(driver_id=driver_filter)
    
    # Contadores
    stats = {
        'total': Delivery.objects.count(),
        # Pending inclui items em_rota (doação em rota) ou coletados/em_transito
        'pending': Delivery.objects.filter(Q(donation__status='em_rota') | Q(status__in=['coletada',])).count(),
        'in_transit': Delivery.objects.filter(status='em_transito').count(),
        'delivered': Delivery.objects.filter(status='entregue').count(),
        'canceled': Delivery.objects.filter(status='cancelada').count(),
    }
    
    # Lista de drivers disponíveis
    drivers = Profile.objects.filter(user_type='transportador', is_available=True).select_related('user')

    # Preparar ítens para template: marcar se pertencem a lote de reciclagem, nome do parceiro
    deliveries_list = []
    for d in deliveries:
        # evitar queries pesadas no template; anexar atributos úteis
        is_recycling = d.donation.recycling_batches.exists()
        recycling_partner_name = None
        if is_recycling:
            latest_batch = d.donation.recycling_batches.order_by('-created_at').first()
            if latest_batch and latest_batch.partner:
                recycling_partner_name = latest_batch.partner.company_name
        d.is_recycling = is_recycling
        d.recycling_partner_name = recycling_partner_name
        # display_status: se donation está em_rota, apresentar 'Em Rota'
        if d.donation and d.donation.status == 'em_rota':
            d.display_status_label = 'Em Rota'
        else:
            d.display_status_label = d.get_status_display()
        deliveries_list.append(d)

    context = {
        'deliveries': deliveries_list,
        'stats': stats,
        'status_filter': status_filter,
        'driver_filter': driver_filter,
        'status_choices': Delivery.STATUS_CHOICES,
        'drivers': drivers,
    }

    return render(request, 'admin/deliveries_management.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def assign_delivery(request, donation_id):
    """
    Atribuir um delivery a um transportador
    """
    donation = get_object_or_404(Donation, pk=donation_id)
    
    # Verificar se já existe delivery
    existing_delivery = Delivery.objects.filter(donation=donation).first()
    if existing_delivery:
        messages.warning(request, 'Esta doação já possui um delivery atribuído.')
        return redirect('admin:admin_deliveries_management')
    
    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        
        if not driver_id:
            messages.error(request, 'Selecione um transportador.')
            return redirect('admin:admin_deliveries_management')
        
        try:
            driver = Profile.objects.get(pk=driver_id, user_type='transportador')
            
            # Criar delivery
            Delivery.objects.create(
                donation=donation,
                driver=driver.user,
                status='atribuida'
            )
            
            # Atualizar status da doação
            donation.status = 'em_rota'
            donation.save()
            
            messages.success(request, f'Delivery atribuído a {driver.user.get_full_name() or driver.user.username}')
            return redirect('admin:admin_deliveries_management')
        except Profile.DoesNotExist:
            messages.error(request, 'Transportador não encontrado.')
            return redirect('admin:admin_deliveries_management')
    
    drivers = Profile.objects.filter(user_type='transportador', is_available=True).select_related('user')
    context = {
        'donation': donation,
        'drivers': drivers,
    }
    return render(request, 'admin/assign_delivery.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def collection_points_management(request):
    """
    Gerenciamento de pontos de coleta
    """
    points = CollectionPoint.objects.annotate(
        item_count=Count('donations')
    ).order_by('name')
    
    # Filtro
    active_only = request.GET.get('active_only', 'on') == 'on'
    if active_only:
        points = points.filter(is_active=True)
    
    context = {
        'points': points,
        'active_only': active_only,
    }
    
    return render(request, 'admin/collection_points.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def approve_donation(request, pk):
    """
    Aprova uma doação diretamente sem passar pelo admin do Django
    """
    donation = get_object_or_404(Donation, pk=pk)
    
    if request.method == 'POST':
        donation.status = 'aprovada'
        donation.save()
        messages.success(request, f'Doação "{donation.title}" aprovada com sucesso!')
        return redirect('doacoes:admin_donations_management')
    
    # Se não for POST, redireciona de volta
    return redirect('doacoes:admin_donations_management')


@user_passes_test(is_admin, login_url='usuario:login')
def reject_donation(request, pk):
    """
    Reprovar uma doação: marca como não reutilizável e direciona para reciclagem
    """
    donation = get_object_or_404(Donation, pk=pk)

    if request.method == 'POST':
        donation.status = 'reciclagem'
        donation.save()
        messages.success(request, f'Doação "{donation.title}" marcada para reciclagem (não reutilizável).')
        return redirect('doacoes:admin_donations_management')

    return redirect('doacoes:admin_donations_management')
