from django.contrib import admin
from .models import Donation, Message, DonationRequest, CollectionPoint, Delivery, RecyclingPartner, RecyclingBatch
from .notifications import (
    notify_donation_approved, notify_donation_rejected,
    notify_request_approved, notify_request_rejected,
    notify_delivery_in_progress, notify_delivery_completed
)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('title', 'donor', 'status', 'city', 'condition', 'created_at')
    list_filter = ('status', 'condition', 'city', 'created_at')
    search_fields = ('title', 'description', 'donor__username', 'contact_email')
    readonly_fields = ('created_at', 'donor', 'approved_by', 'approved_at')
    fieldsets = (
        ('Informações da Doação', {
            'fields': ('title', 'description', 'condition', 'image', 'donor')
        }),
        ('Contato', {
            'fields': ('contact_email', 'contact_phone', 'city')
        }),
        ('Entrega', {
            'fields': ('delivery_type', 'collection_point', 'pickup_address', 'pickup_latitude', 'pickup_longitude')
        }),
        ('Status e Aprovação', {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Se mudou o status para aprovada
            if obj.status == 'aprovada' and not obj.approved_by:
                obj.approved_by = request.user
                obj.approved_at = admin.timezone.now()
                notify_donation_approved(obj)
            # Se mudou para rejeitada
            elif obj.status == 'cancelada':
                notify_donation_rejected(obj, 'Cancelada pelo administrador')
        super().save_model(request, obj, form, change)


@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'donation', 'beneficiary', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('donation__title', 'beneficiary__username', 'reason')
    readonly_fields = ('created_at', 'updated_at', 'beneficiary', 'donation')
    fieldsets = (
        ('Solicitação', {
            'fields': ('donation', 'beneficiary', 'reason')
        }),
        ('Aprovação/Rejeição', {
            'fields': ('status', 'approved_by', 'rejection_reason')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            if obj.status == 'aprovada' and not obj.approved_by:
                obj.approved_by = request.user
                notify_request_approved(obj)
            elif obj.status == 'rejeitada':
                notify_request_rejected(obj, obj.rejection_reason or 'Rejeitada pelo administrador')
        super().save_model(request, obj, form, change)


@admin.register(CollectionPoint)
class CollectionPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_active', 'current_inventory', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'address', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    fieldsets = (
        ('Informações', {
            'fields': ('name', 'address', 'phone', 'email')
        }),
        ('Localização', {
            'fields': ('latitude', 'longitude')
        }),
        ('Operação', {
            'fields': ('opening_hours', 'capacity', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'donation', 'sender', 'recipient', 'has_image', 'created_at', 'read')
    list_filter = ('created_at', 'read', 'donation')
    search_fields = ('text', 'sender__username', 'recipient__username', 'donation__title')
    readonly_fields = ('created_at', 'sender', 'recipient', 'donation')
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.short_description = 'Com imagem'
    has_image.boolean = True


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'donation', 'driver', 'status', 'assigned_at', 'delivered_at')
    list_filter = ('status', 'assigned_at', 'delivered_at')
    search_fields = ('donation__title', 'driver__username', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'assigned_at')
    fieldsets = (
        ('Informações de Entrega', {
            'fields': ('donation', 'driver', 'status')
        }),
        ('Coleta', {
            'fields': ('picked_up_at', 'pickup_latitude', 'pickup_longitude')
        }),
        ('Entrega', {
            'fields': ('delivered_at', 'delivery_latitude', 'delivery_longitude', 'proof_image', 'signature_image')
        }),
        ('Observações', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            # Se mudou para em_transito
            if obj.status == 'em_transito':
                notify_delivery_in_progress(obj.donation)
            # Se mudou para entregue
            elif obj.status == 'entregue':
                obj.donation.status = 'entregue'
                obj.donation.save()
                notify_delivery_completed(obj.donation)
        super().save_model(request, obj, form, change)


@admin.register(RecyclingPartner)
class RecyclingPartnerAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'cnpj', 'phone', 'is_active', 'max_monthly_capacity_kg')
    list_filter = ('is_active',)
    search_fields = ('company_name', 'cnpj', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RecyclingBatch)
class RecyclingBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_code', 'partner', 'status', 'estimated_weight_kg', 'actual_weight_kg', 'created_at')
    list_filter = ('status', 'partner', 'created_at')
    search_fields = ('batch_code', 'partner__company_name')
    readonly_fields = ('created_at', 'updated_at', 'collected_at', 'sent_at', 'processed_at', 'certificate_issued_at')
    filter_horizontal = ('items',)