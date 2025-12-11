"""
Views para o painel do transportador/motorista
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .models import Delivery
from usuario.models import Profile


def is_driver(user):
    """Verifica se o usuário é transportador"""
    try:
        return user.profile.user_type == 'transportador'
    except (AttributeError, Profile.DoesNotExist):
        return False


@login_required
@user_passes_test(is_driver, login_url='usuario:login')
def driver_dashboard(request):
    """
    Dashboard do transportador com entregas atribuídas
    """
    # Entregas do motorista
    deliveries = Delivery.objects.filter(driver=request.user).select_related(
        'donation', 'donation__donor'
    ).order_by('-created_at')
    
    # Estatísticas
    stats = {
        'pending': deliveries.filter(status__in=['atribuida', 'coletada']).count(),
        'in_transit': deliveries.filter(status='em_transito').count(),
        'completed': deliveries.filter(status='entregue').count(),
        'total': deliveries.count(),
    }
    
    # Entregas ativas (não entregues/canceladas)
    active_deliveries = deliveries.exclude(status__in=['entregue', 'cancelada'])
    
    # Histórico recente
    recent_deliveries = deliveries.filter(status__in=['entregue', 'cancelada'])[:10]
    
    context = {
        'stats': stats,
        'active_deliveries': active_deliveries,
        'recent_deliveries': recent_deliveries,
    }
    
    return render(request, 'driver/dashboard.html', context)


@login_required
@user_passes_test(is_driver, login_url='usuario:login')
def delivery_detail(request, pk):
    """
    Detalhes de uma entrega específica
    """
    delivery = get_object_or_404(
        Delivery.objects.select_related('donation', 'donation__donor'),
        pk=pk,
        driver=request.user
    )
    
    # Obter beneficiário da solicitação aprovada
    beneficiary_request = delivery.donation.donationrequest_set.filter(
        status='aprovada'
    ).select_related('beneficiary').first()
    
    context = {
        'delivery': delivery,
        'beneficiary_request': beneficiary_request,
    }
    
    return render(request, 'driver/delivery_detail.html', context)


@login_required
@user_passes_test(is_driver, login_url='usuario:login')
def update_delivery_status(request, pk):
    """
    Atualizar status de uma entrega
    """
    delivery = get_object_or_404(Delivery, pk=pk, driver=request.user)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        
        # Validar transição de status
        valid_transitions = {
            'atribuida': ['coletada', 'cancelada'],
            'coletada': ['em_transito', 'cancelada'],
            'em_transito': ['entregue', 'cancelada'],
        }
        
        if new_status in valid_transitions.get(delivery.status, []):
            old_status = delivery.status
            delivery.status = new_status
            
            # Atualizar timestamps específicos
            if new_status == 'coletada':
                delivery.pickup_time = timezone.now()
                delivery.pickup_latitude = request.POST.get('latitude')
                delivery.pickup_longitude = request.POST.get('longitude')
            elif new_status == 'entregue':
                delivery.delivery_time = timezone.now()
                delivery.delivery_latitude = request.POST.get('latitude')
                delivery.delivery_longitude = request.POST.get('longitude')
                
                # Atualizar status da doação
                delivery.donation.status = 'entregue'
                delivery.donation.save()
                
                # Atualizar solicitação
                approved_request = delivery.donation.donationrequest_set.filter(
                    status='aprovada'
                ).first()
                if approved_request:
                    approved_request.status = 'entregue'
                    approved_request.save()
            
            delivery.save()
            
            messages.success(
                request,
                f'Status atualizado de "{delivery.get_status_display_for(old_status)}" para "{delivery.get_status_display()}"'
            )
        else:
            messages.error(request, 'Transição de status inválida')
        
        return redirect('doacoes:driver_delivery_detail', pk=delivery.pk)
    
    return redirect('doacoes:driver_dashboard')


@login_required
@user_passes_test(is_driver, login_url='usuario:login')
def upload_proof(request, pk):
    """
    Upload de comprovante de entrega (foto e assinatura)
    """
    delivery = get_object_or_404(Delivery, pk=pk, driver=request.user)
    
    if request.method == 'POST':
        if 'proof_image' in request.FILES:
            delivery.proof_image = request.FILES['proof_image']
        
        if 'signature_image' in request.FILES:
            delivery.signature_image = request.FILES['signature_image']
        
        delivery.notes = request.POST.get('notes', '')
        delivery.save()
        
        messages.success(request, 'Comprovante de entrega enviado com sucesso!')
        return redirect('doacoes:driver_delivery_detail', pk=delivery.pk)
    
    context = {
        'delivery': delivery,
    }
    
    return render(request, 'driver/upload_proof.html', context)


@login_required
@user_passes_test(is_driver, login_url='usuario:login')
def toggle_availability(request):
    """
    Alternar disponibilidade do motorista
    """
    try:
        profile = request.user.profile
        profile.is_available = not profile.is_available
        profile.save()
        
        status = 'disponível' if profile.is_available else 'indisponível'
        messages.success(request, f'Você está agora {status} para receber entregas')
    except Profile.DoesNotExist:
        messages.error(request, 'Perfil não encontrado')
    
    return redirect('doacoes:driver_dashboard')
