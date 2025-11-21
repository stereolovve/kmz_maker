from django.contrib import admin
from django.utils.html import format_html
from .models import KMLJob


@admin.register(KMLJob)
class KMLJobAdmin(admin.ModelAdmin):
    """Admin interface para KMLJob"""

    list_display = [
        'id',
        'process_type_display',
        'status_badge',
        'processed_items',
        'skipped_items',
        'routes_created',
        'created_at',
        'download_link',
    ]

    list_filter = [
        'status',
        'process_type',
        'created_at',
    ]

    search_fields = [
        'id',
        'error_message',
    ]

    readonly_fields = [
        'id',
        'status',
        'total_items',
        'processed_items',
        'skipped_items',
        'routes_created',
        'error_message',
        'created_at',
        'updated_at',
        'completed_at',
        'output_file',
    ]

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('id', 'process_type', 'status', 'input_file')
        }),
        ('Estatísticas', {
            'fields': ('total_items', 'processed_items', 'skipped_items', 'routes_created')
        }),
        ('Resultado', {
            'fields': ('output_file', 'error_message')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )

    def process_type_display(self, obj):
        """Display do tipo de processamento"""
        return obj.get_process_type_display()
    process_type_display.short_description = 'Tipo'

    def status_badge(self, obj):
        """Badge colorido para status"""
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def download_link(self, obj):
        """Link para download do arquivo"""
        if obj.status == 'completed' and obj.output_file:
            return format_html(
                '<a href="{}" target="_blank">Download KML</a>',
                obj.output_file.url
            )
        return '-'
    download_link.short_description = 'Download'

    def has_add_permission(self, request):
        """Não permitir criação manual via admin"""
        return False
