from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import os

from .models import KMLJob
from .serializers import KMLJobSerializer, KMLJobCreateSerializer
from .services import process_excel_com_rotas, process_excel_simples


def home_view(request):
    """View para a página inicial HTML"""
    return render(request, 'home.html')


def tutorial_view(request):
    """View para a página de tutorial"""
    return render(request, 'tutorial.html')


class KMLJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para processamento de arquivos Excel e geração de KML

    Endpoints:
    - POST /api/kml/process/ - Upload Excel e processar
    - GET /api/kml/jobs/ - Listar todos os jobs
    - GET /api/kml/jobs/{id}/ - Detalhes de um job
    - GET /api/kml/jobs/{id}/download/ - Download do KML gerado
    """

    queryset = KMLJob.objects.all()
    serializer_class = KMLJobSerializer

    @swagger_auto_schema(
        method='post',
        operation_description="""
        Upload de arquivo Excel e processamento para KML.

        Tipos de processamento:
        - 'rotas': Gera KML com rotas usando Google Maps API (requer coordenadas inicial e final)
        - 'simples': Gera KML apenas com pontos (requer apenas coordenadas iniciais)

        O arquivo Excel deve conter as seguintes colunas:
        - Obrigatórias: tipo, ano, kmi, lati, longi
        - Opcionais: kmf, latf, longf, sentido
        """,
        request_body=KMLJobCreateSerializer,
        responses={
            201: openapi.Response(
                description="Job criado e processado com sucesso",
                schema=KMLJobSerializer
            ),
            400: "Erro de validação ou processamento"
        }
    )
    @action(detail=False, methods=['post'])
    def process(self, request):
        """Upload e processamento de arquivo Excel"""

        serializer = KMLJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Criar job
        job = serializer.save(status='processing')

        try:
            # Obter caminhos
            input_path = job.input_file.path
            output_filename = f"output_{job.id}.kml"
            log_filename = f"log_{job.id}.txt"
            output_path = os.path.join(os.path.dirname(input_path), output_filename)
            log_path = os.path.join(os.path.dirname(input_path), log_filename)

            # Processar conforme tipo
            if job.process_type == 'rotas':
                stats = process_excel_com_rotas(input_path, output_path, log_path)
                job.routes_created = stats.get('routes_created', 0)
            else:  # simples
                stats = process_excel_simples(input_path, output_path, log_path)

            # Atualizar job com estatísticas
            job.status = 'completed'
            job.total_items = stats.get('total', 0)
            job.processed_items = stats.get('processed', 0)
            job.skipped_items = stats.get('skipped', 0)
            job.completed_at = timezone.now()

            # Salvar arquivo de output
            from django.core.files import File
            with open(output_path, 'rb') as f:
                job.output_file.save(output_filename, File(f), save=False)

            # Salvar arquivo de log
            if os.path.exists(log_path):
                with open(log_path, 'rb') as f:
                    job.log_file.save(log_filename, File(f), save=False)

            job.save()

            # Limpar arquivos temporários
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(log_path):
                os.remove(log_path)

            return Response(
                KMLJobSerializer(job).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.save()

            return Response(
                {'error': str(e), 'job_id': str(job.id)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Download do arquivo KML gerado",
        responses={
            200: openapi.Response(
                description="Arquivo KML",
                schema=openapi.Schema(type=openapi.TYPE_FILE)
            ),
            404: "Job não encontrado ou arquivo não disponível"
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download do arquivo KML gerado"""

        job = self.get_object()

        if job.status != 'completed' or not job.output_file:
            return Response(
                {'error': 'Arquivo não disponível. Verifique o status do job.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return FileResponse(
            job.output_file.open('rb'),
            as_attachment=True,
            filename=f'obras_{job.process_type}_{job.created_at.strftime("%Y%m%d")}.kml'
        )

    @swagger_auto_schema(
        operation_description="Download do arquivo de log do processamento",
        responses={
            200: openapi.Response(
                description="Arquivo de log (.txt)",
                schema=openapi.Schema(type=openapi.TYPE_FILE)
            ),
            404: "Job não encontrado ou log não disponível"
        }
    )
    @action(detail=True, methods=['get'])
    def download_log(self, request, pk=None):
        """Download do arquivo de log gerado"""

        job = self.get_object()

        if job.status != 'completed' or not job.log_file:
            return Response(
                {'error': 'Arquivo de log não disponível. Verifique o status do job.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return FileResponse(
            job.log_file.open('rb'),
            as_attachment=True,
            filename=f'log_{job.process_type}_{job.created_at.strftime("%Y%m%d")}.txt'
        )
