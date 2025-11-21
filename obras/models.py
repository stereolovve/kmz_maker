from django.db import models
import uuid


class KMLJob(models.Model):
    """Model para rastrear jobs de processamento de KML"""

    PROCESS_TYPE_CHOICES = [
        ('rotas', 'Com Rotas (Google Maps)'),
        ('simples', 'Simples (Apenas Pontos)'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('processing', 'Processando'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    process_type = models.CharField(max_length=10, choices=PROCESS_TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    # Arquivos
    input_file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    output_file = models.FileField(upload_to='outputs/%Y/%m/%d/', null=True, blank=True)
    log_file = models.FileField(upload_to='logs/%Y/%m/%d/', null=True, blank=True)

    # Estatísticas
    total_items = models.IntegerField(default=0)
    processed_items = models.IntegerField(default=0)
    skipped_items = models.IntegerField(default=0)
    routes_created = models.IntegerField(default=0, null=True, blank=True)

    # Mensagens
    error_message = models.TextField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'KML Job'
        verbose_name_plural = 'KML Jobs'

    def __str__(self):
        return f"{self.get_process_type_display()} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
