from django.contrib import admin
from .models import SenderAccount, EmailLog


@admin.register(SenderAccount)
class SenderAccountAdmin(admin.ModelAdmin):
    list_display = [
        'email', 'display_name', 'daily_limit',
        'is_active', 'created_at',
    ]
    list_filter = ['is_active']
    search_fields = ['email', 'display_name']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_email', 'recipient_name', 'subject',
        'status', 'batch_label', 'sender_account',
        'sent_at', 'created_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = [
        'recipient_email', 'recipient_name', 'subject', 'batch_label']
    readonly_fields = [
        'batch_id', 'recipient_email', 'recipient_name', 'subject',
        'template_name', 'status', 'sender_account', 'sent_by',
        'sent_at', 'error_message', 'created_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
