"""
Views para relatórios e análise de impacto do ReCo
"""
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .models import Donation, DonationRequest, Delivery


def is_admin(user):
    """Verifica se o usuário é administrador"""
    return user.is_staff or user.is_superuser


@user_passes_test(is_admin, login_url='usuario:login')
def reports_dashboard(request):
    """
    Dashboard de relatórios com visão geral
    """
    # Período selecionado (padrão: últimos 30 dias)
    period = request.GET.get('period', '30')
    
    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
        period_name = 'Últimos 7 dias'
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
        period_name = 'Últimos 30 dias'
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
        period_name = 'Últimos 90 dias'
    elif period == '365':
        start_date = timezone.now() - timedelta(days=365)
        period_name = 'Último ano'
    else:  # all
        start_date = None
        period_name = 'Todo o período'
    
    # Base queryset
    if start_date:
        donations_qs = Donation.objects.filter(created_at__gte=start_date)
        requests_qs = DonationRequest.objects.filter(created_at__gte=start_date)
        deliveries_qs = Delivery.objects.filter(created_at__gte=start_date)
    else:
        donations_qs = Donation.objects.all()
        requests_qs = DonationRequest.objects.all()
        deliveries_qs = Delivery.objects.all()
    
    # Estatísticas principais
    total_donations = donations_qs.count()
    total_approved = donations_qs.filter(status='aprovada').count()
    total_delivered = donations_qs.filter(status='entregue').count()
    total_requests = requests_qs.count()
    total_deliveries = deliveries_qs.filter(status='entregue').count()
    
    # Usuários únicos
    unique_donors = donations_qs.values('donor').distinct().count()
    unique_beneficiaries = requests_qs.values('beneficiary').distinct().count()
    
    # Impacto ambiental
    # Estimativa: 3kg por item eletrônico
    estimated_kg = total_delivered * 3
    # CO2 evitado: 60kg de CO2 por kg de eletrônico reciclado
    estimated_co2 = estimated_kg * 60
    # Energia economizada: 15 kWh por kg
    estimated_energy = estimated_kg * 15
    
    # Taxa de aprovação
    approval_rate = (total_approved / total_donations * 100) if total_donations > 0 else 0
    delivery_rate = (total_delivered / total_approved * 100) if total_approved > 0 else 0
    
    # Doações por condição
    donations_by_condition = donations_qs.values('condition').annotate(count=Count('id')).order_by('-count')
    
    # Doações por status
    donations_by_status = donations_qs.values('status').annotate(count=Count('id')).order_by('-count')
    
    context = {
        'period': period,
        'period_name': period_name,
        'start_date': start_date,
        'stats': {
            'total_donations': total_donations,
            'total_approved': total_approved,
            'total_delivered': total_delivered,
            'total_requests': total_requests,
            'total_deliveries': total_deliveries,
            'unique_donors': unique_donors,
            'unique_beneficiaries': unique_beneficiaries,
            'approval_rate': round(approval_rate, 1),
            'delivery_rate': round(delivery_rate, 1),
        },
        'impact': {
            'estimated_kg': estimated_kg,
            'estimated_co2': estimated_co2,
            'estimated_energy': estimated_energy,
        },
        'donations_by_condition': list(donations_by_condition),
        'donations_by_status': list(donations_by_status),
    }
    
    return render(request, 'reports/dashboard.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def donation_report(request):
    """
    Relatório detalhado de doações
    """
    # Filtros
    period = request.GET.get('period', '30')
    status_filter = request.GET.get('status', '')
    condition_filter = request.GET.get('condition', '')
    
    # Período
    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
    elif period == '365':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = None
    
    # Queryset base
    donations = Donation.objects.select_related('donor', 'approved_by')
    
    if start_date:
        donations = donations.filter(created_at__gte=start_date)
    if status_filter:
        donations = donations.filter(status=status_filter)
    if condition_filter:
        donations = donations.filter(condition=condition_filter)
    
    donations = donations.order_by('-created_at')
    
    # Análise temporal (por dia)
    daily_stats = defaultdict(int)
    for donation in donations:
        date_key = donation.created_at.date()
        daily_stats[date_key] += 1
    
    # Converter para lista ordenada
    daily_data = [
        {'date': date.strftime('%d/%m'), 'count': count}
        for date, count in sorted(daily_stats.items())
    ]
    
    # Top doadores
    top_donors = donations.values('donor__username', 'donor__first_name', 'donor__last_name')\
        .annotate(count=Count('id'))\
        .order_by('-count')[:10]
    
    # Estatísticas por condição
    condition_stats = donations.values('condition')\
        .annotate(count=Count('id'))\
        .order_by('-count')
    
    context = {
        'donations': donations[:100],  # Limitar para performance
        'total_count': donations.count(),
        'daily_data': daily_data,
        'top_donors': top_donors,
        'condition_stats': list(condition_stats),
        'period': period,
        'status_filter': status_filter,
        'condition_filter': condition_filter,
        'status_choices': Donation.STATUS_CHOICES,
        'condition_choices': Donation.CONDITION_CHOICES,
    }
    
    return render(request, 'reports/donations.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def impact_report(request):
    """
    Relatório de impacto ambiental
    """
    # Filtros
    period = request.GET.get('period', '30')
    
    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
    elif period == '365':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = None
    
    # Doações entregues (impacto real)
    delivered_donations = Donation.objects.filter(status='entregue')
    if start_date:
        delivered_donations = delivered_donations.filter(created_at__gte=start_date)
    
    total_delivered = delivered_donations.count()
    
    # Cálculos de impacto
    # Premissas:
    # - 3kg por item eletrônico médio
    # - 60kg CO2 por kg de eletrônico reciclado
    # - 15 kWh de energia economizada por kg
    # - 500L de água economizada por kg
    # - 0.05 árvores salvas por kg
    
    kg_total = total_delivered * 3
    co2_avoided = kg_total * 60  # kg de CO2
    energy_saved = kg_total * 15  # kWh
    water_saved = kg_total * 500  # Litros
    trees_saved = kg_total * 0.05  # Árvores equivalentes
    
    # Impacto por categoria (condição)
    impact_by_condition = delivered_donations.values('condition')\
        .annotate(count=Count('id'))\
        .order_by('-count')
    
    # Adicionar cálculos
    for item in impact_by_condition:
        item['kg'] = item['count'] * 3
        item['co2'] = item['kg'] * 60
    
    # Evolução mensal
    monthly_impact = defaultdict(lambda: {'count': 0, 'kg': 0, 'co2': 0})
    for donation in delivered_donations:
        month_key = donation.created_at.strftime('%Y-%m')
        monthly_impact[month_key]['count'] += 1
        monthly_impact[month_key]['kg'] += 3
        monthly_impact[month_key]['co2'] += 180
    
    # Converter para lista ordenada
    monthly_data = [
        {
            'month': datetime.strptime(month, '%Y-%m').strftime('%b/%Y'),
            'count': data['count'],
            'kg': data['kg'],
            'co2': data['co2']
        }
        for month, data in sorted(monthly_impact.items())
    ]
    
    # Beneficiários impactados
    unique_beneficiaries = DonationRequest.objects.filter(
        donation__in=delivered_donations,
        status='entregue'
    ).values('beneficiary').distinct().count()
    
    context = {
        'period': period,
        'total_delivered': total_delivered,
        'impact': {
            'kg_total': kg_total,
            'co2_avoided': round(co2_avoided, 2),
            'energy_saved': round(energy_saved, 2),
            'water_saved': round(water_saved, 2),
            'trees_saved': round(trees_saved, 2),
        },
        'impact_by_condition': list(impact_by_condition),
        'monthly_data': monthly_data,
        'unique_beneficiaries': unique_beneficiaries,
    }
    
    return render(request, 'reports/impact.html', context)


@user_passes_test(is_admin, login_url='usuario:login')
def export_donations_excel(request):
    """Exporta relatório de doações em Excel (XLSX)"""
    period = request.GET.get('period', '30')
    status_filter = request.GET.get('status', '')
    condition_filter = request.GET.get('condition', '')

    # Período
    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
    elif period == '365':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = None

    donations = Donation.objects.select_related('donor')
    if start_date:
        donations = donations.filter(created_at__gte=start_date)
    if status_filter:
        donations = donations.filter(status=status_filter)
    if condition_filter:
        donations = donations.filter(condition=condition_filter)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Doacoes'

    headers = ['ID', 'Título', 'Doado por', 'Status', 'Condição', 'Cidade', 'Criado em']
    ws.append(headers)

    for donation in donations.order_by('-created_at'):
        ws.append([
            donation.id,
            donation.title,
            donation.donor.get_full_name() or donation.donor.username,
            donation.get_status_display(),
            donation.get_condition_display(),
            donation.city,
            donation.created_at.strftime('%d/%m/%Y'),
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"relatorio-doacoes-{timezone.now().strftime('%Y%m%d-%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


@user_passes_test(is_admin, login_url='usuario:login')
def export_impact_pdf(request):
    """Exporta relatório de impacto ambiental em PDF"""
    period = request.GET.get('period', '30')

    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
    elif period == '365':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = None

    delivered = Donation.objects.filter(status='entregue')
    if start_date:
        delivered = delivered.filter(created_at__gte=start_date)

    total = delivered.count()
    kg_total = total * 3
    impact = {
        'CO2 evitado (kg)': kg_total * 60,
        'Energia economizada (kWh)': kg_total * 15,
        'Água economizada (L)': kg_total * 500,
        'Árvores preservadas': kg_total * 0.05,
    }

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Relatório de Impacto Ambiental', styles['Title']))
    elements.append(Paragraph(f'Período: {period}', styles['Normal']))
    elements.append(Paragraph(f'Data de geração: {timezone.now().strftime("%d/%m/%Y %H:%M")}', styles['Normal']))
    elements.append(Spacer(1, 12))

    data = [['Indicador', 'Valor']]
    data.append(['Itens entregues', total])
    data.append(['Peso estimado (kg)', kg_total])
    for key, value in impact.items():
        data.append([key, f"{value:,.1f}" if isinstance(value, float) else value])

    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F2B705')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    filename = f"impacto-ambiental-{timezone.now().strftime('%Y%m%d-%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response


@user_passes_test(is_admin, login_url='usuario:login')
def beneficiary_report(request):
    """
    Relatório de beneficiários
    """
    # Filtros
    period = request.GET.get('period', '30')
    
    if period == '7':
        start_date = timezone.now() - timedelta(days=7)
    elif period == '30':
        start_date = timezone.now() - timedelta(days=30)
    elif period == '90':
        start_date = timezone.now() - timedelta(days=90)
    elif period == '365':
        start_date = timezone.now() - timedelta(days=365)
    else:
        start_date = None
    
    # Solicitações
    requests = DonationRequest.objects.select_related('beneficiary', 'donation')
    if start_date:
        requests = requests.filter(created_at__gte=start_date)
    
    # Top beneficiários
    top_beneficiaries = requests.values(
        'beneficiary__username',
        'beneficiary__first_name',
        'beneficiary__last_name'
    ).annotate(
        total_requests=Count('id'),
        approved_requests=Count('id', filter=Q(status='aprovada')),
        delivered_requests=Count('id', filter=Q(status='entregue'))
    ).order_by('-delivered_requests')[:20]
    
    # Taxa de aprovação por beneficiário
    for beneficiary in top_beneficiaries:
        if beneficiary['total_requests'] > 0:
            beneficiary['approval_rate'] = round(
                beneficiary['approved_requests'] / beneficiary['total_requests'] * 100, 1
            )
        else:
            beneficiary['approval_rate'] = 0
    
    # Estatísticas gerais
    total_beneficiaries = requests.values('beneficiary').distinct().count()
    total_requests = requests.count()
    approved_requests = requests.filter(status='aprovada').count()
    delivered_requests = requests.filter(status='entregue').count()
    
    # Solicitações por status
    requests_by_status = requests.values('status')\
        .annotate(count=Count('id'))\
        .order_by('-count')
    
    context = {
        'period': period,
        'stats': {
            'total_beneficiaries': total_beneficiaries,
            'total_requests': total_requests,
            'approved_requests': approved_requests,
            'delivered_requests': delivered_requests,
            'approval_rate': round(approved_requests / total_requests * 100, 1) if total_requests > 0 else 0,
        },
        'top_beneficiaries': top_beneficiaries,
        'requests_by_status': list(requests_by_status),
    }
    
    return render(request, 'reports/beneficiaries.html', context)
