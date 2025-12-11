from django.urls import path
from . import views
from . import request_views
from . import admin_views
from . import reports_views
from . import recycling_views
from . import driver_views
from . import recycling_views

app_name = 'doacoes'

urlpatterns = [
    # Listagem e detalhes de doações
    path('', views.index, name='index'),
    path('novo/', views.create, name='create'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/editar/', views.edit_donation, name='edit_donation'),
    path('<int:pk>/excluir/', views.delete_donation, name='delete_donation'),
    
    # Pontos de coleta
    path('mapa/', views.collection_points_map, name='collection_points_map'),
    
    # Solicitações de doação
    path('<int:pk>/solicitar/', request_views.request_donation, name='request_donation'),
    path('minhas-solicitacoes/', request_views.my_requests, name='my_requests'),
    path('solicitacao/<int:pk>/', request_views.request_detail, name='request_detail'),
    path('solicitacao/<int:pk>/aprovar/', request_views.approve_request, name='approve_request'),
    path('solicitacao/<int:pk>/rejeitar/', request_views.reject_request, name='reject_request'),
    
    # Painel do doador
    path('minhas-doacoes/', request_views.my_donations, name='my_donations'),
    
    # Painel administrativo
    path('admin/dashboard/', admin_views.dashboard, name='admin_dashboard'),
    path('admin/doacoes/', admin_views.donations_management, name='admin_donations_management'),
    path('admin/doacoes/<int:pk>/aprovar/', admin_views.approve_donation, name='admin_approve_donation'),
    path('admin/solicitacoes/', admin_views.requests_management, name='admin_requests_management'),
    path('admin/entregas/', admin_views.deliveries_management, name='admin_deliveries_management'),
    path('admin/entregas/<int:donation_id>/atribuir/', admin_views.assign_delivery, name='admin_assign_delivery'),
    path('admin/pontos-coleta/', admin_views.collection_points_management, name='admin_collection_points'),
    
    # Relatórios
    path('relatorios/', reports_views.reports_dashboard, name='reports_dashboard'),
    path('relatorios/doacoes/', reports_views.donation_report, name='reports_donations'),
    path('relatorios/impacto/', reports_views.impact_report, name='reports_impact'),
    path('relatorios/beneficiarios/', reports_views.beneficiary_report, name='reports_beneficiaries'),
    path('relatorios/exportar/doacoes.xlsx', reports_views.export_donations_excel, name='reports_export_donations'),
    path('relatorios/exportar/impacto.pdf', reports_views.export_impact_pdf, name='reports_export_impact'),

    # Painel do transportador
    path('transportador/', driver_views.driver_dashboard, name='driver_dashboard'),
    path('transportador/entrega/<int:pk>/', driver_views.delivery_detail, name='driver_delivery_detail'),
    path('transportador/entrega/<int:pk>/status/', driver_views.update_delivery_status, name='driver_update_delivery_status'),
    path('transportador/entrega/<int:pk>/comprovante/', driver_views.upload_proof, name='driver_upload_proof'),
    path('transportador/disponibilidade/', driver_views.toggle_availability, name='driver_toggle_availability'),

    # Reciclagem
    path('reciclagem/', recycling_views.recycling_dashboard, name='recycling_dashboard'),
    path('reciclagem/novo-lote/', recycling_views.create_batch, name='recycling_create_batch'),
    path('reciclagem/lote/<int:pk>/', recycling_views.batch_detail, name='recycling_batch_detail'),
    path('reciclagem/lote/<int:pk>/status/', recycling_views.update_batch_status, name='recycling_update_batch_status'),
    path('reciclagem/lote/<int:pk>/certificado/', recycling_views.upload_certificate, name='recycling_upload_certificate'),
    path('reciclagem/parceiros/', recycling_views.partner_list, name='recycling_partner_list'),
    path('reciclagem/parceiros/<int:pk>/', recycling_views.partner_detail, name='recycling_partner_detail'),
    path('reciclagem/marcar/<int:donation_id>/', recycling_views.mark_item_for_recycling, name='recycling_mark_item'),
    path('reciclagem/relatorio/', recycling_views.recycling_report, name='recycling_report'),
    
    # Chat e mensagens
    path('chats/', views.chats, name='chats'),
    path('<int:pk>/chat/', views.chat, name='chat'),
    path('<int:donation_pk>/doar/<int:beneficiary_pk>/', views.select_beneficiary, name='select_beneficiary'),
    path('<int:pk>/messages/', views.messages_json, name='messages_json'),
    path('<int:pk>/messages/send/', views.post_message, name='post_message'),
    
    # Sistema de Reciclagem
    path('reciclagem/', recycling_views.recycling_dashboard, name='recycling_dashboard'),
    path('reciclagem/lotes/criar/', recycling_views.create_batch, name='recycling_create_batch'),
    path('reciclagem/lotes/<int:pk>/', recycling_views.batch_detail, name='recycling_batch_detail'),
    path('reciclagem/lotes/<int:pk>/atualizar-status/', recycling_views.update_batch_status, name='recycling_update_batch_status'),
    path('reciclagem/lotes/<int:pk>/certificado/', recycling_views.upload_certificate, name='recycling_upload_certificate'),
    path('reciclagem/parceiros/', recycling_views.partner_list, name='recycling_partner_list'),
    path('reciclagem/parceiros/<int:pk>/', recycling_views.partner_detail, name='recycling_partner_detail'),
    path('reciclagem/marcar/<int:donation_id>/', recycling_views.mark_item_for_recycling, name='recycling_mark_item'),
    path('reciclagem/relatorio/', recycling_views.recycling_report, name='recycling_report'),
]
