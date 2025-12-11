"""
Sistema de notificações por email para ReCo
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_email_notification(subject, template_name, context, recipient_email):
    """
    Envia email com base em um template
    
    Args:
        subject: Assunto do email
        template_name: Nome do template HTML (ex: 'email/donation_approved.html')
        context: Dicionário com dados para o template
        recipient_email: Email do destinatário
    """
    try:
        # Renderizar o template HTML
        html_message = render_to_string(template_name, context)
        # Criar versão em texto simples
        plain_message = strip_tags(html_message)
        
        # Enviar email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False


def notify_donation_approved(donation):
    """Notifica doador que sua doação foi aprovada"""
    context = {
        'donor_name': donation.donor.get_full_name() or donation.donor.username,
        'donation_title': donation.title,
        'donation_id': donation.pk,
        'status': donation.get_status_display(),
    }
    send_email_notification(
        subject='Sua doação foi aprovada! 🎉',
        template_name='email/donation_approved.html',
        context=context,
        recipient_email=donation.donor.email,
    )


def notify_donation_rejected(donation, rejection_reason=''):
    """Notifica doador que sua doação foi rejeitada"""
    context = {
        'donor_name': donation.donor.get_full_name() or donation.donor.username,
        'donation_title': donation.title,
        'donation_id': donation.pk,
        'rejection_reason': rejection_reason,
    }
    send_email_notification(
        subject='Sua doação foi rejeitada',
        template_name='email/donation_rejected.html',
        context=context,
        recipient_email=donation.donor.email,
    )


def notify_request_approved(donation_request):
    """Notifica beneficiário que sua solicitação foi aprovada"""
    context = {
        'beneficiary_name': donation_request.beneficiary.get_full_name() or donation_request.beneficiary.username,
        'donation_title': donation_request.donation.title,
        'donation_id': donation_request.donation.pk,
        'donation_condition': donation_request.donation.get_condition_display(),
    }
    send_email_notification(
        subject='Sua solicitação foi aprovada! ✅',
        template_name='email/request_approved.html',
        context=context,
        recipient_email=donation_request.beneficiary.email,
    )


def notify_request_rejected(donation_request, rejection_reason=''):
    """Notifica beneficiário que sua solicitação foi rejeitada"""
    context = {
        'beneficiary_name': donation_request.beneficiary.get_full_name() or donation_request.beneficiary.username,
        'donation_title': donation_request.donation.title,
        'rejection_reason': rejection_reason,
    }
    send_email_notification(
        subject='Sua solicitação foi rejeitada',
        template_name='email/request_rejected.html',
        context=context,
        recipient_email=donation_request.beneficiary.email,
    )


def notify_delivery_in_progress(donation):
    """Notifica doador e beneficiário que a entrega está em andamento"""
    beneficiary_email = None
    try:
        # Tentar encontrar o beneficiário aprovado
        request = donation.requests.filter(status='aprovada').first()
        if request:
            beneficiary_email = request.beneficiary.email
            beneficiary_name = request.beneficiary.get_full_name() or request.beneficiary.username
        else:
            beneficiary_name = "Beneficiário"
    except Exception:
        beneficiary_name = "Beneficiário"
    
    context = {
        'donor_name': donation.donor.get_full_name() or donation.donor.username,
        'beneficiary_name': beneficiary_name,
        'donation_title': donation.title,
        'donation_id': donation.pk,
    }
    
    # Notificar doador
    send_email_notification(
        subject='Sua doação está em rota! 🚚',
        template_name='email/delivery_in_progress.html',
        context=context,
        recipient_email=donation.donor.email,
    )
    
    # Notificar beneficiário se encontrado
    if beneficiary_email:
        send_email_notification(
            subject='Sua doação está chegando! 🚚',
            template_name='email/delivery_in_progress_beneficiary.html',
            context=context,
            recipient_email=beneficiary_email,
        )


def notify_delivery_completed(donation):
    """Notifica doador e beneficiário que a entrega foi concluída"""
    beneficiary_email = None
    try:
        request = donation.requests.filter(status='aprovada').first()
        if request:
            beneficiary_email = request.beneficiary.email
            beneficiary_name = request.beneficiary.get_full_name() or request.beneficiary.username
        else:
            beneficiary_name = "Beneficiário"
    except Exception:
        beneficiary_name = "Beneficiário"
    
    context = {
        'donor_name': donation.donor.get_full_name() or donation.donor.username,
        'beneficiary_name': beneficiary_name,
        'donation_title': donation.title,
        'donation_id': donation.pk,
    }
    
    # Notificar doador
    send_email_notification(
        subject='Sua doação foi entregue com sucesso! ✅',
        template_name='email/delivery_completed.html',
        context=context,
        recipient_email=donation.donor.email,
    )
    
    # Notificar beneficiário se encontrado
    if beneficiary_email:
        send_email_notification(
            subject='Sua doação chegou! ✅',
            template_name='email/delivery_completed_beneficiary.html',
            context=context,
            recipient_email=beneficiary_email,
        )


def notify_new_request(donation_request):
    """Notifica admin sobre nova solicitação"""
    # Pegar email de todos os admins
    from django.contrib.auth.models import User
    admins = User.objects.filter(is_staff=True)
    
    context = {
        'beneficiary_name': donation_request.beneficiary.get_full_name() or donation_request.beneficiary.username,
        'donation_title': donation_request.donation.title,
        'donation_id': donation_request.donation.pk,
        'reason': donation_request.reason,
    }
    
    for admin in admins:
        if admin.email:
            send_email_notification(
                subject=f'Nova solicitação para aprovação: {donation_request.donation.title}',
                template_name='email/new_request_admin.html',
                context=context,
                recipient_email=admin.email,
            )


def send_recycling_notification(batch, old_status, new_status):
    """Notifica responsáveis sobre mudança de status do lote de reciclagem"""
    recipients = []
    if batch.created_by and batch.created_by.email:
        recipients.append(batch.created_by.email)
    if batch.partner and batch.partner.email:
        recipients.append(batch.partner.email)
    # Evitar duplicados
    recipients = list(dict.fromkeys(recipients))

    if not recipients:
        return

    subject = f'Lote {batch.batch_code} atualizado para {batch.get_status_display()}'
    message = (
        f'O lote {batch.batch_code} mudou de {old_status} para {new_status}.\n'
        f'Parceiro: {batch.partner.company_name}\n'
        f'Itens: {batch.total_items()}\n'
        f'Peso estimado: {batch.estimated_weight_kg} kg'
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception:
        # Silenciar falhas para não quebrar fluxo de atualização
        pass
