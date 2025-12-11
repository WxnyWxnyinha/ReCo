"""
Views para gerenciamento de solicitações de doação
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Donation, DonationRequest
from .forms import DonationRequestForm
from .notifications import notify_new_request, notify_request_approved, notify_request_rejected


def is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_staff or user.is_superuser


@login_required(login_url='usuario:login')
@require_http_methods(["GET", "POST"])
def request_donation(request, pk):
    """
    Beneficiário solicita uma doação
    """
    donation = get_object_or_404(Donation, pk=pk, status='aprovada')
    
    # Não permitir que o doador solicite sua própria doação
    if donation.donor == request.user:
        messages.error(request, 'Você não pode solicitar sua própria doação.')
        return redirect('doacoes:detail', pk=pk)
    
    # Verificar se já existe solicitação
    existing_request = DonationRequest.objects.filter(
        donation=donation,
        beneficiary=request.user
    ).first()
    
    if existing_request:
        if existing_request.status == 'pendente':
            messages.info(request, 'Você já solicitou este item. Aguarde a análise.')
        elif existing_request.status == 'aprovada':
            messages.info(request, 'Você já foi aprovado para receber este item!')
        elif existing_request.status == 'rejeitada':
            messages.warning(request, 'Sua solicitação anterior foi rejeitada. Você pode tentar novamente.')
        return redirect('doacoes:detail', pk=pk)
    
    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            donation_request = form.save(commit=False)
            donation_request.donation = donation
            donation_request.beneficiary = request.user
            donation_request.save()
            
            # Notificar admin
            notify_new_request(donation_request)
            
            messages.success(request, 'Solicitação enviada com sucesso! Aguarde a análise do administrador.')
            return redirect('doacoes:detail', pk=pk)
    else:
        form = DonationRequestForm()
    
    context = {
        'donation': donation,
        'form': form,
    }
    return render(request, 'marketplace/request_donation.html', context)


@login_required(login_url='usuario:login')
def my_requests(request):
    """
    Painel do beneficiário com suas solicitações
    """
    # Filtrar por status
    status_filter = request.GET.get('status', '')
    
    requests = DonationRequest.objects.filter(
        beneficiary=request.user
    ).select_related('donation', 'donation__donor', 'approved_by').order_by('-created_at')
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
        'status_choices': DonationRequest.STATUS_CHOICES,
    }
    return render(request, 'marketplace/my_requests.html', context)


@login_required(login_url='usuario:login')
def request_detail(request, pk):
    """
    Detalhe de uma solicitação específica
    """
    donation_request = get_object_or_404(
        DonationRequest.objects.select_related('donation', 'beneficiary', 'approved_by'),
        pk=pk
    )
    
    # Verificar permissão
    is_owner = donation_request.beneficiary == request.user
    is_donor = donation_request.donation.donor == request.user
    is_admin = request.user.is_staff
    
    if not (is_owner or is_donor or is_admin):
        messages.error(request, 'Você não tem permissão para acessar esta solicitação.')
        return redirect('doacoes:index')
    
    context = {
        'donation_request': donation_request,
        'is_owner': is_owner,
        'is_donor': is_donor,
        'is_admin': is_admin,
    }
    return render(request, 'marketplace/request_detail.html', context)


@login_required(login_url='usuario:login')
def my_donations(request):
    """
    Painel do doador com suas doações e solicitações recebidas
    """
    donations = Donation.objects.filter(
        donor=request.user
    ).prefetch_related('requests').order_by('-created_at')
    
    # Adiciona count de aprovadas em cada doação
    for donation in donations:
        donation.approved_requests_count = donation.requests.filter(status='aprovada').count()
    
    # Estatísticas
    stats = {
        'total_donations': donations.count(),
        'approved_donations': donations.filter(status='aprovada').count(),
        'pending_donations': donations.filter(status='pendente').count(),
        'delivered_donations': donations.filter(status='entregue').count(),
        'total_requests': sum(d.requests.count() for d in donations),
        'pending_requests': sum(
            d.requests.filter(status='pendente').count() for d in donations
        ),
        'approved_requests': sum(
            d.requests.filter(status='aprovada').count() for d in donations
        ),
    }
    
    context = {
        'donations': donations,
        'stats': stats,
    }
    return render(request, 'marketplace/my_donations.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
@require_http_methods(["POST"])
def approve_request(request, pk):
    """
    Admin aprova uma solicitação (POST only)
    """
    donation_request = get_object_or_404(DonationRequest, pk=pk)
    
    donation_request.status = 'aprovada'
    donation_request.approved_by = request.user
    donation_request.save()
    
    # Notificar beneficiário
    notify_request_approved(donation_request)
    
    messages.success(request, 'Solicitação aprovada e beneficiário notificado!')
    return redirect('doacoes:request_detail', pk=pk)


@user_passes_test(is_admin, login_url='usuario:login')
@require_http_methods(["GET", "POST"])
def reject_request(request, pk):
    """
    Admin rejeita uma solicitação
    """
    donation_request = get_object_or_404(DonationRequest, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Rejeitada pelo administrador')
        donation_request.status = 'rejeitada'
        donation_request.rejection_reason = reason
        donation_request.approved_by = request.user
        donation_request.save()
        
        # Notificar beneficiário
        notify_request_rejected(donation_request, reason)
        
        messages.success(request, 'Solicitação rejeitada.')
        return redirect('doacoes:request_detail', pk=pk)
    
    context = {
        'donation_request': donation_request,
    }
    return render(request, 'marketplace/reject_request.html', context)
