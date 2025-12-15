from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import DonationForm, MessageForm
from .models import Donation, Message, CollectionPoint


User = get_user_model()


def index(request):
    """Listar anúncios com filtros simples de busca, condição e cidade."""
    # Excluir doações que já foram entregues, reprovadas (reciclagem) ou que estão em análise
    # Excluir entregues, em rota, marcadas para reciclagem (status ou associadas a lote) e pendentes
    donations = (
        Donation.objects.filter(is_available=True)
        .exclude(status__in=['entregue', 'em_rota', 'reciclagem', 'pendente'])
        .exclude(recycling_batches__isnull=False)
        .distinct()
    )
    search = (request.GET.get('q') or '').strip()
    condition = request.GET.get('condition') or ''
    city = (request.GET.get('city') or '').strip()
    order = request.GET.get('order') or 'recent'

    if search:
        donations = donations.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    if condition:
        donations = donations.filter(condition=condition)
    if city:
        donations = donations.filter(city__icontains=city)

    if order == 'oldest':
        donations = donations.order_by('created_at')
    elif order == 'name':
        donations = donations.order_by('title')
    else:
        donations = donations.order_by('-created_at')

    city_choices = (
        Donation.objects.exclude(city='').exclude(city__isnull=True)
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    # Verificar se o usuário autenticado tem doações
    user_has_donations = False
    if request.user.is_authenticated:
        user_has_donations = Donation.objects.filter(donor=request.user).exists()

    context = {
        'donations': donations.select_related('donor'),
        'filters': {
            'search': search,
            'condition': condition,
            'city': city,
            'order': order,
        },
        'city_choices': city_choices,
        'condition_choices': Donation.CONDITION_CHOICES,
        'user_has_donations': user_has_donations,
    }
    return render(request, 'marketplace/index.html', context)


def create_redirect(request):
    """Compatibilidade com URLs antigas: redireciona /doacoes/create -> novo/"""
    return redirect('/doacoes/novo/')


@login_required(login_url='usuario:login')
def create(request):
    """Criar um novo anúncio de doação."""
    # Permitir criação apenas por usuários do tipo 'doador'
    user_type = None
    try:
        user_type = getattr(request.user, 'profile', None) and request.user.profile.user_type
    except Exception:
        user_type = None

    if user_type != 'doador':
        messages.error(request, 'Apenas usuários do tipo Doador podem cadastrar doações.')
        return redirect('doacoes:index')

    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            # Anti-duplicação: evita criar anúncio com mesmo título pelo mesmo usuário
            title = (form.cleaned_data.get('title') or '').strip()
            duplicate_exists = Donation.objects.filter(
                donor=request.user,
                title__iexact=title,
                status__in=['pendente', 'aprovada', 'em_rota'],
            ).exists()
            if duplicate_exists:
                messages.error(request, 'Você já possui um anúncio semelhante ativo ou em análise. Evite duplicar anúncios.')
                return render(request, 'marketplace/create.html', {'form': form})

            donation = form.save(commit=False)
            donation.donor = request.user
            donation.save()
            messages.success(request, 'Anúncio publicado com sucesso!')
            return redirect('doacoes:detail', donation.pk)
    else:
        form = DonationForm()

    return render(request, 'marketplace/create.html', {'form': form})


def detail(request, pk):
    donation = get_object_or_404(
        Donation.objects.select_related('donor'),
        pk=pk,
    )
    # Relacionados visíveis (mesmos filtros do feed)
    related = (
        Donation.objects.filter(is_available=True)
        .exclude(pk=pk)
        .exclude(status__in=['entregue', 'em_rota', 'reciclagem', 'pendente'])
        .exclude(recycling_batches__isnull=False)
        .distinct()
        .order_by('-created_at')[:3]
    )

    # Permissões de UI: dono pode abrir chats com interessados; outros só se forem participantes
    is_owner = request.user.is_authenticated and donation.donor == request.user
    participants = list(_participants_for_donation(donation)) if is_owner else list(_participants_for_donation(donation)) if request.user.is_authenticated and request.user in _participants_for_donation(donation) else []

    can_chat = False
    if request.user.is_authenticated:
        # Administradores podem abrir chat com o doador para suporte
        if request.user.is_staff or request.user.is_superuser:
            can_chat = True
        elif is_owner:
            # dono sempre vê o link para abrir a área de chat (seleciona participante depois)
            can_chat = True
        else:
            # Interessados do tipo beneficiário ou PJ podem iniciar conversa para tirar dúvidas
            try:
                ut = request.user.profile.user_type
            except Exception:
                ut = None
            if ut in ('beneficiario', 'pj') and donation.is_available and donation.status not in ['entregue', 'reciclagem', 'em_rota'] and not donation.recycling_batches.exists():
                can_chat = True
            else:
                # interessado só vê chat se já for participante (mensagens ou solicitação aprovada)
                can_chat = request.user in participants

    # Beneficiário/ONG/PJ podem solicitar o item (apenas estes tipos), e somente se estiver disponível
    can_request = False
    try:
        user_type = request.user.profile.user_type if request.user.is_authenticated else None
    except Exception:
        user_type = None
    if (
        request.user.is_authenticated
        and not is_owner
        and user_type in ('beneficiario', 'pj')
        and donation.is_available
        and donation.status not in ['entregue', 'reciclagem', 'em_rota']
        and not donation.recycling_batches.exists()
    ):
        can_request = True

    context = {
        'donation': donation,
        'related': related,
        'is_owner': is_owner,
        'can_chat': can_chat,
        'can_request': can_request,
    }
    return render(request, 'marketplace/detail.html', context)


@login_required(login_url='usuario:login')
def chats(request):
    """Resumo das conversas do usuário (como doador ou interessado)."""
    user = request.user
    latest = (
        Message.objects.filter(Q(sender=user) | Q(recipient=user))
        .select_related('donation', 'donation__donor', 'sender', 'recipient')
        .order_by('-created_at')
    )

    conversations = {}
    for msg in latest:
        other = msg.recipient if msg.sender == user else msg.sender
        if other is None:
            continue
        key = (msg.donation_id, other.id)
        stored = conversations.get(key)
        if not stored or msg.created_at > stored['last_message'].created_at:
            conversations[key] = {
                'donation': msg.donation,
                'other': other,
                'last_message': msg,
            }

    ordered = sorted(
        conversations.values(),
        key=lambda item: item['last_message'].created_at,
        reverse=True,
    )

    return render(request, 'marketplace/chats.html', {'conversations': ordered})


def _participants_for_donation(donation):
    """
    Retorna usuários (exceto o doador) que:
    1. Têm DonationRequest aprovada (pessoas interessadas)
    2. Ou que já trocaram mensagens nesse anúncio
    """
    # Beneficiários com solicitação aprovada
    approved_beneficiaries = set(
        donation.requests.filter(status='aprovada').values_list('beneficiary_id', flat=True)
    )
    
    # Usuários que já trocaram mensagens
    user_ids = set(
        donation.messages.values_list('sender_id', flat=True)
    ) | set(
        donation.messages.values_list('recipient_id', flat=True)
    )
    user_ids.discard(donation.donor_id)
    
    # Combina ambos os grupos
    all_user_ids = approved_beneficiaries | user_ids
    
    if not all_user_ids:
        return User.objects.none()
    return User.objects.filter(id__in=all_user_ids)


def _resolve_partner(request, donation, participant_id):
    """Determina o interlocutor da conversa conforme o usuário logado."""
    if request.user == donation.donor:
        if not participant_id:
            return None, JsonResponse(
                {'error': 'Selecione um interessado para continuar o chat.'},
                status=400,
            )
        try:
            participant = User.objects.get(pk=participant_id)
        except User.DoesNotExist:
            return None, JsonResponse({'error': 'Usuário não encontrado.'}, status=404)
        if participant == request.user:
            return None, JsonResponse({'error': 'Conversa inválida.'}, status=400)
        valid_ids = set(_participants_for_donation(donation).values_list('id', flat=True))
        if participant.id not in valid_ids:
            return None, JsonResponse(
                {'error': 'Esse interessado ainda não iniciou conversa.'},
                status=400,
            )
        return participant, None

    # Interessado falando com o doador
    if participant_id and str(participant_id) != str(donation.donor_id):
        return None, JsonResponse({'error': 'Conversa inválida.'}, status=400)
    return donation.donor, None


@login_required(login_url='usuario:login')
def chat(request, pk):
    donation = get_object_or_404(Donation.objects.select_related('donor'), pk=pk)
    is_owner = donation.donor == request.user
    participants = list(_participants_for_donation(donation)) if is_owner else []

    active_participant = None
    participant_param = request.GET.get('with')

    if is_owner:
        if participant_param:
            active_participant = next(
                (p for p in participants if str(p.pk) == participant_param),
                None,
            )
        if not active_participant and participants:
            active_participant = participants[0]
    else:
        active_participant = donation.donor

    messages_url = reverse('doacoes:messages_json', kwargs={'pk': donation.pk})
    post_url = reverse('doacoes:post_message', kwargs={'pk': donation.pk})

    if active_participant:
        messages_url = f"{messages_url}?participant={active_participant.pk}"
        post_url = f"{post_url}?participant={active_participant.pk}"

    context = {
        'donation': donation,
        'form': MessageForm(),
        'is_owner': is_owner,
        'participants': participants,
        'active_participant': active_participant,
        'messages_url': messages_url if active_participant else None,
        'post_url': post_url if active_participant else None,
    }

    if is_owner and not active_participant:
        messages.info(
            request,
            'Nenhum interessado iniciou conversa ainda. Volte quando receber mensagens.',
        )

    return render(request, 'marketplace/chat.html', context)


@login_required(login_url='usuario:login')
def messages_json(request, pk):
    donation = get_object_or_404(Donation, pk=pk)
    participant_id = request.GET.get('participant')
    other, error_response = _resolve_partner(request, donation, participant_id)
    if error_response:
        return error_response

    qs = (
        Message.objects.filter(donation=donation)
        .filter(
            Q(sender=request.user, recipient=other)
            | Q(sender=other, recipient=request.user)
        )
        .order_by('created_at')
        .select_related('sender')
    )

    data = [
        {
            'id': msg.id,
            'sender': msg.sender.get_full_name() or msg.sender.get_username(),
            'sender_id': msg.sender.id,
            'text': msg.text,
            'image': msg.image.url if msg.image else None,
            'created_at': msg.created_at.isoformat(),
        }
        for msg in qs
    ]
    return JsonResponse({'messages': data})


@login_required(login_url='usuario:login')
def post_message(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido.'}, status=405)

    donation = get_object_or_404(Donation, pk=pk)
    participant_id = request.GET.get('participant')
    other, error_response = _resolve_partner(request, donation, participant_id)
    if error_response:
        return error_response

    form = MessageForm(request.POST, request.FILES)
    if not form.is_valid():
        # Retornar erros de validação para debug
        errors = ', '.join([f"{field}: {error[0]}" for field, error in form.errors.items()])
        return JsonResponse({'error': f'Mensagem inválida. {errors}'}, status=400)

    message = form.save(commit=False)
    message.donation = donation
    message.sender = request.user
    message.recipient = other
    message.save()

    return JsonResponse({'ok': True})


def collection_points_map(request):
    """
    Exibir mapa interativo com pontos de coleta
    """
    points = CollectionPoint.objects.filter(is_active=True).annotate(
        current_inventory=Count('donations', filter=Q(donations__status__in=['pendente', 'aprovada']))
    )
    
    context = {
        'points': points,
    }
    
    return render(request, 'marketplace/map.html', context)


@login_required(login_url='usuario:login')
def edit_donation(request, pk):
    """Editar uma doação existente."""
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    
    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Doação atualizada com sucesso!')
            return redirect('doacoes:detail', pk=donation.pk)
    else:
        form = DonationForm(instance=donation)
    
    return render(request, 'marketplace/edit_donation.html', {'form': form, 'donation': donation})


@login_required(login_url='usuario:login')
def delete_donation(request, pk):
    """Excluir uma doação."""
    donation = get_object_or_404(Donation, pk=pk, donor=request.user)
    
    if request.method == 'POST':
        donation.delete()
        messages.success(request, 'Doação removida com sucesso!')
        return redirect('doacoes:my_donations')
    
    return render(request, 'marketplace/confirm_delete_donation.html', {'donation': donation})


@login_required(login_url='usuario:login')
def select_beneficiary(request, donation_pk, beneficiary_pk):
    """Doador seleciona beneficiário para receber a doação."""
    donation = get_object_or_404(Donation, pk=donation_pk, donor=request.user)
    beneficiary = get_object_or_404(User, pk=beneficiary_pk)
    
    # Verifica se beneficiário tem solicitação aprovada
    donation_request = donation.requests.filter(beneficiary=beneficiary, status='aprovada').first()
    
    if not donation_request:
        messages.error(request, 'Este beneficiário não tem solicitação aprovada para este item.')
        return redirect('doacoes:chat', pk=donation.pk)
    
    # Marca o beneficiário escolhido — o doador libera o item para este beneficiário
    donation.beneficiary = beneficiary
    donation.save()

    # Atualiza a solicitação para 'aprovada' pelo doador; o admin precisa finalizar a aprovação/elogística
    donation_request.status = 'aprovada'
    donation_request.approved_by = request.user
    donation_request.save()

    messages.success(
        request,
        f'Você selecionou {beneficiary.get_full_name() or beneficiary.username} como beneficiário. ' 
        'Aguardando aprovação final do administrador para processar a logística.'
    )

    return redirect('doacoes:chat', pk=donation.pk)
