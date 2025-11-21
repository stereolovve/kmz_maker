from rest_framework import serializers
from .models import KMLJob


class KMLJobSerializer(serializers.ModelSerializer):
    """Serializer para leitura de KMLJob"""

    process_type_display = serializers.CharField(source='get_process_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = KMLJob
        fields = [
            'id',
            'process_type',
            'process_type_display',
            'status',
            'status_display',
            'input_file',
            'output_file',
            'log_file',
            'total_items',
            'processed_items',
            'skipped_items',
            'routes_created',
            'error_message',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'output_file',
            'log_file',
            'total_items',
            'processed_items',
            'skipped_items',
            'routes_created',
            'error_message',
            'created_at',
            'updated_at',
            'completed_at',
        ]


class KMLJobCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de KMLJob"""

    input_file = serializers.FileField(required=True)
    process_type = serializers.ChoiceField(
        choices=KMLJob.PROCESS_TYPE_CHOICES,
        required=True,
        help_text="Tipo de processamento: 'rotas' (com rotas Google Maps) ou 'simples' (apenas pontos)"
    )

    class Meta:
        model = KMLJob
        fields = ['input_file', 'process_type']

    def validate_input_file(self, value):
        """Validar extensão do arquivo"""
        if not value.name.endswith(('.xlsx', '.xls')):
            raise serializers.ValidationError("Apenas arquivos Excel (.xlsx, .xls) são aceitos.")
        return value
