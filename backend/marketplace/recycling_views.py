"""
Views para o sistema de reciclagem
Gerenciamento de lotes de itens não reutilizáveis enviados para parceiros de reciclagem
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import RecyclingBatch, RecyclingPartner, Donation
from .notifications import send_recycling_notification


def is_staff_user(user):
    """Verifica se o usuário é staff (admin)"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_user)
def recycling_dashboard(request):
    """Dashboard principal de reciclagem"""
    # Estatísticas gerais
    total_batches = RecyclingBatch.objects.count()
    active_batches = RecyclingBatch.objects.exclude(status='certificado').count()
    total_partners = RecyclingPartner.objects.filter(is_active=True).count()
    
    # Peso total processado
    total_weight = RecyclingBatch.objects.aggregate(
        total=Sum('actual_weight_kg')
    )['total'] or 0
    
    # Impacto ambiental total
    environmental_impact = {
        'co2_avoided_kg': total_weight * 60,
        'energy_saved_kwh': total_weight * 15,
        'water_saved_liters': total_weight * 500,
        'trees_preserved': total_weight * 0.05,
    }
    
    # Lotes recentes
    recent_batches = RecyclingBatch.objects.select_related('partner', 'created_by')[:10]
    
    # Parceiros ativos
    partners = RecyclingPartner.objects.filter(is_active=True).annotate(
        total_batches=Count('batches'),
        total_weight=Sum('batches__actual_weight_kg')
    ).order_by('-total_batches')[:5]
    
    # Itens candidatos à reciclagem (doações marcadas como 'reciclagem')
    items_for_recycling = Donation.objects.filter(status='reciclagem').count()
    
    context = {
        'total_batches': total_batches,
        'active_batches': active_batches,
        'total_partners': total_partners,
        'total_weight': total_weight,
        'environmental_impact': environmental_impact,
        'recent_batches': recent_batches,
        'partners': partners,
        'items_for_recycling': items_for_recycling,
    }
    
    return render(request, 'marketplace/recycling/dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def create_batch(request):
    """Criar novo lote de reciclagem"""
    if request.method == 'POST':
        partner_id = request.POST.get('partner')
        partner = get_object_or_404(RecyclingPartner, pk=partner_id, is_active=True)
        
        # Gerar código único do lote
        today = datetime.now()
        batch_code = f"REC-{today.year}{today.month:02d}{today.day:02d}-{RecyclingBatch.objects.count() + 1:04d}"
        
        # Criar lote
        batch = RecyclingBatch.objects.create(
            batch_code=batch_code,
            partner=partner,
            created_by=request.user,
            notes=request.POST.get('notes', '')
        )
        
        # Adicionar itens selecionados
        item_ids = request.POST.getlist('items')
        if item_ids:
            items = Donation.objects.filter(pk__in=item_ids, status='reciclagem')
            batch.items.set(items)
            batch.update_estimated_weight()
            
            # Atualizar status dos itens
            items.update(status='em_rota')  # Em rota para reciclagem
        
        messages.success(request, f'Lote {batch.batch_code} criado com sucesso!')
        return redirect('recycling_batch_detail', pk=batch.pk)
    
    # GET request
    partners = RecyclingPartner.objects.filter(is_active=True)
    items = Donation.objects.filter(status='reciclagem').order_by('-created_at')
    
    context = {
        'partners': partners,
        'items': items,
    }
    
    return render(request, 'marketplace/recycling/create_batch.html', context)


@login_required
@user_passes_test(is_staff_user)
def batch_detail(request, pk):
    """Detalhes de um lote de reciclagem"""
    batch = get_object_or_404(RecyclingBatch.objects.select_related('partner', 'created_by', 'processed_by'), pk=pk)
    
    # Calcular impacto ambiental
    impact = batch.calculate_environmental_impact()
    
    context = {
        'batch': batch,
        'impact': impact,
    }
    
    return render(request, 'marketplace/recycling/batch_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def update_batch_status(request, pk):
    """Atualizar status do lote"""
    if request.method != 'POST':
        return redirect('recycling_batch_detail', pk=pk)
    
    batch = get_object_or_404(RecyclingBatch, pk=pk)
    new_status = request.POST.get('status')
    
    # Validar transições de status
    valid_transitions = {
        'criado': ['coletado'],
        'coletado': ['enviado'],
        'enviado': ['processado'],
        'processado': ['certificado'],
    }
    
    if new_status not in valid_transitions.get(batch.status, []):
        messages.error(request, 'Transição de status inválida!')
        return redirect('recycling_batch_detail', pk=pk)
    
    # Atualizar status e timestamps
    old_status = batch.status
    batch.status = new_status
    
    if new_status == 'coletado':
        batch.collected_at = timezone.now()
    elif new_status == 'enviado':
        batch.sent_at = timezone.now()
    elif new_status == 'processado':
        batch.processed_at = timezone.now()
        batch.processed_by = request.user
        # Registrar peso real
        actual_weight = request.POST.get('actual_weight')
        if actual_weight:
            batch.actual_weight_kg = float(actual_weight)
    elif new_status == 'certificado':
        batch.certificate_number = request.POST.get('certificate_number', '')
        batch.certificate_issued_at = timezone.now()
    
    batch.save()
    
    # Enviar notificação
    send_recycling_notification(batch, old_status, new_status)
    
    messages.success(request, f'Status atualizado para {batch.get_status_display()}!')
    return redirect('recycling_batch_detail', pk=pk)


@login_required
@user_passes_test(is_staff_user)
def upload_certificate(request, pk):
    """Upload do certificado de reciclagem"""
    if request.method != 'POST':
        return redirect('recycling_batch_detail', pk=pk)
    
    batch = get_object_or_404(RecyclingBatch, pk=pk)
    
    if 'certificate_file' in request.FILES:
        batch.certificate_file = request.FILES['certificate_file']
        batch.certificate_number = request.POST.get('certificate_number', batch.certificate_number)
        batch.certificate_issued_at = timezone.now()
        batch.status = 'certificado'
        batch.save()
        
        messages.success(request, 'Certificado enviado com sucesso!')
    else:
        messages.error(request, 'Nenhum arquivo selecionado!')
    
    return redirect('recycling_batch_detail', pk=pk)


@login_required
@user_passes_test(is_staff_user)
def partner_list(request):
    """Listar parceiros de reciclagem"""
    partners = RecyclingPartner.objects.annotate(
        total_batches=Count('batches'),
        total_weight=Sum('batches__actual_weight_kg')
    ).order_by('-total_batches')
    
    context = {
        'partners': partners,
    }
    
    return render(request, 'marketplace/recycling/partner_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def partner_detail(request, pk):
    """Detalhes do parceiro de reciclagem"""
    partner = get_object_or_404(RecyclingPartner, pk=pk)
    
    # Lotes do parceiro
    batches = RecyclingBatch.objects.filter(partner=partner).select_related('created_by')
    
    # Estatísticas
    total_weight = batches.aggregate(total=Sum('actual_weight_kg'))['total'] or 0
    total_items = sum(batch.total_items() for batch in batches)
    
    context = {
        'partner': partner,
        'batches': batches,
        'total_weight': total_weight,
        'total_items': total_items,
    }
    
    return render(request, 'marketplace/recycling/partner_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def mark_item_for_recycling(request, donation_id):
    """Marcar item como candidato à reciclagem"""
    if request.method != 'POST':
        return redirect('admin_donations_management')
    
    donation = get_object_or_404(Donation, pk=donation_id)
    
    # Validar que o item não está em processo de doação
    if donation.status in ['em_rota', 'entregue']:
        messages.error(request, 'Este item já está em processo de entrega!')
        return redirect('admin_donations_management')
    
    # Marcar para reciclagem
    donation.status = 'reciclagem'
    donation.save()
    
    messages.success(request, f'Item "{donation.title}" marcado para reciclagem!')
    return redirect('admin_donations_management')


@login_required
@user_passes_test(is_staff_user)
def recycling_report(request):
    """Relatório de reciclagem com impacto ambiental"""
    # Filtro de período
    period = request.GET.get('period', '30')
    
    if period == 'all':
        batches = RecyclingBatch.objects.all()
    else:
        days = int(period)
        start_date = timezone.now() - timedelta(days=days)
        batches = RecyclingBatch.objects.filter(created_at__gte=start_date)
    
    # Estatísticas
    total_batches = batches.count()
    certified_batches = batches.filter(status='certificado').count()
    total_weight = batches.aggregate(total=Sum('actual_weight_kg'))['total'] or 0
    total_items = sum(batch.total_items() for batch in batches)
    
    # Impacto ambiental
    environmental_impact = {
        'co2_avoided_kg': total_weight * 60,
        'energy_saved_kwh': total_weight * 15,
        'water_saved_liters': total_weight * 500,
        'trees_preserved': total_weight * 0.05,
    }
    
    # Distribuição por parceiro
    partner_stats = RecyclingPartner.objects.filter(
        batches__in=batches
    ).annotate(
        batch_count=Count('batches'),
        total_weight=Sum('batches__actual_weight_kg')
    ).order_by('-total_weight')
    
    context = {
        'period': period,
        'total_batches': total_batches,
        'certified_batches': certified_batches,
        'total_weight': total_weight,
        'total_items': total_items,
        'environmental_impact': environmental_impact,
        'partner_stats': partner_stats,
    }
    
    return render(request, 'marketplace/recycling/report.html', context)
