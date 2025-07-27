import json
import logging # Adicionado para logging

from django.contrib.auth import authenticate
from django.db.models import Q # Adicionado para queries complexas
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import RefreshToken

# --- Imports Atualizados ---
# Adicionados UploadedFile e os novos Serializers
from .models import Aluno, CasoClinico, Diagnostico, Professor, Turma, Usuario, Equipe, UploadedFile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework import status, filters
from .serializers import TurmaSerializer, EquipeSerializer, AlunoSerializer, FileUploadSerializer, FileListSerializer
# Adicionadas as Class-Based Views e Parsers para o upload
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status

# Configuração do Logger
logger = logging.getLogger(__name__)




@csrf_exempt
@require_http_methods(['POST'])
def cadastro(request):
    try:
        data = json.loads(request.body)
        # ... (seu código de cadastro continua aqui, sem alterações)
        first_name = data.get('nome')
        last_name = data.get('sobrenome', '')
        cpf = data.get('cpf')
        email = data.get('email')
        password = data.get('senha')
        username = data.get('username')
        foto_url = data.get('foto_url', '')
        tipo_usuario_str = data.get('tipo')

        if not all([first_name, cpf, email, password, username, tipo_usuario_str]):
            return JsonResponse(
                {'erro': 'Campos obrigatórios ausentes (nome, cpf, email, senha, username, tipo).'},
                status=400,
            )

        if Usuario.objects.filter(email=email).exists():
            return JsonResponse({'erro': 'Este email já está cadastrado.'}, status=400)
        if Usuario.objects.filter(username=username).exists():
            return JsonResponse({'erro': 'Este nome de usuário já está em uso.'}, status=400)
        if Usuario.objects.filter(cpf=cpf).exists():
            return JsonResponse({'erro': 'Este CPF já está cadastrado.'}, status=400)

        user_creation_data = {
            'first_name': first_name,
            'last_name': last_name,
            'cpf': cpf,
            'foto_url': foto_url,
        }

        try:
            novo_usuario_obj = Usuario.objects.create_user(
                username=username, email=email, password=password, **user_creation_data
            )
        except ValueError as ve:
            return JsonResponse({'erro': str(ve)}, status=400)

        if tipo_usuario_str == Usuario.Tipo.ALUNO.value:
            novo_usuario_obj.tipo = Usuario.Tipo.ALUNO
            novo_usuario_obj.save()
            Aluno.objects.create(
                usuario=novo_usuario_obj,
                semestre=data.get('semestre', 'N/A'),
                matricula=data.get('matricula', 'N/A'), # Supondo que você também envie a matrícula
            )
        elif tipo_usuario_str == Usuario.Tipo.PROFESSOR.value:
            novo_usuario_obj.tipo = Usuario.Tipo.PROFESSOR
            novo_usuario_obj.save()
            Professor.objects.create(
                usuario=novo_usuario_obj,
                formacao=data.get('formacao', 'N/A'),
                especialidade=data.get('especialidade', 'N/A'),
            )
        elif tipo_usuario_str == Usuario.Tipo.ADMINISTRADOR.value:
            novo_usuario_obj.tipo = Usuario.Tipo.ADMINISTRADOR
            novo_usuario_obj.is_staff = True
            novo_usuario_obj.is_superuser = data.get('is_superuser', False)
            novo_usuario_obj.save()
        else:
            novo_usuario_obj.delete()
            return JsonResponse({'erro': 'Tipo de usuário inválido fornecido.'}, status=400)

        return JsonResponse(
            { 'mensagem': 'Usuário cadastrado com sucesso!', 'usuario': { 'id': novo_usuario_obj.id, 'first_name': novo_usuario_obj.first_name, 'email': novo_usuario_obj.email, 'username': novo_usuario_obj.username, }, }, status=201, )

    except json.JSONDecodeError:
        return JsonResponse({'erro': 'Dados JSON inválidos.'}, status=400)
    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    senha_fornecida = request.data.get('senha')
    if not email or not senha_fornecida:
        return Response( {'erro': 'Email e senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST )

    usuario = authenticate(request, username=email, password=senha_fornecida)

    if usuario is not None:
        refresh = RefreshToken.for_user(usuario)
        user_data_response = { 'id': usuario.id, 'first_name': usuario.first_name, 'last_name': usuario.last_name, 'email': usuario.email, 'username': usuario.username, 'tipo': usuario.tipo, }
        return Response( { 'mensagem': 'Login bem-sucedido!', 'usuario': user_data_response, 'access': str(refresh.access_token), 'refresh': str(refresh), }, status=status.HTTP_200_OK, )
    else:
        return Response( {'erro': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED )

@require_http_methods(['GET'])
def info_perfil_prof(request, id):
    try:
        professor = Professor.objects.get(usuario_id=id)
        dados = { 'nome': f'{professor.usuario.first_name} {professor.usuario.last_name}', 'email': professor.usuario.email, 'formacao': professor.formacao, 'especialidade': professor.especialidade, }
        return JsonResponse(dados)
    except Professor.DoesNotExist:
        raise Http404('Professor não encontrado.')
    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_turmas_prof(request, id):
    try:
        professor_profile = request.user.professor
        turmas = Turma.objects.filter(professor_responsavel=professor_profile)
        turmas_professor = []
        for turma in turmas:
            turmas_professor.append( {'id': turma.id, 'disciplina': turma.disciplina, 'semestre': turma.semestre} )
        return Response(turmas_professor)
    except Professor.DoesNotExist:
        return Response( {'erro': 'Perfil de professor não encontrado para este usuário.'}, status=status.HTTP_404_NOT_FOUND )
    except Exception as e:
        return Response( {'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR )

@require_http_methods(['GET'])
def listar_casos_prof(request, id):
    try:
        professor = Professor.objects.get(usuario_id=id)
        casos = CasoClinico.objects.filter(professor_responsavel=professor)
        casos_professor = []
        for caso in casos:
            casos_professor.append({'id': caso.id, 'título': caso.titulo})
        return JsonResponse(casos_professor, safe=False)
    except Professor.DoesNotExist:
        raise Http404('Professor não encontrado.')
    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)

@require_http_methods(['GET'])
def info_casos(request, prof_id, caso_id):
    # NOTA: O campo 'arquivos' aqui é o antigo JSONField. Para usar os novos uploads,
    # você precisará acessar `caso.materiais_upload.all()` e serializá-los.
    try:
        caso = CasoClinico.objects.get(id=caso_id)
        diagnostico = Diagnostico.objects.get(caso_clinico=caso)
        dados = { 'id': caso.id, 'título': caso.titulo, 'descrição': caso.descricao, 'area': caso.area, 'arquivos': caso.arquivos, 'dificuldade': caso.dificuldade, 'diagnóstico': diagnostico.descricao, }
        return JsonResponse(dados)
    except Professor.DoesNotExist:
        raise Http404('Professor não encontrado.')
    except CasoClinico.DoesNotExist:
        raise Http404('Caso clínico não encontrado.')
    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def info_turmas(request, id):
    try:
        turma = Turma.objects.select_related('professor_responsavel__usuario').prefetch_related('alunos_matriculados__usuario').get(id=id)
        serializer = TurmaSerializer(turma)
        return Response(serializer.data)
    except Turma.DoesNotExist:
        return Response( {'erro': 'Turma não encontrada.'}, status=status.HTTP_404_NOT_FOUND )

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def listar_equipes_da_turma(request, turma_id):
    if request.method == 'GET':
        equipes = Equipe.objects.filter(
            turma_id=turma_id
        ).prefetch_related(
            'alunos__usuario'
        )

        if not equipes.exists():
            return Response([], status=status.HTTP_200_OK)

        serializer = EquipeSerializer(equipes, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        try:
            turma = Turma.objects.get(pk=turma_id)
        except Turma.DoesNotExist:
            return Response({'erro': 'Turma não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        nome_equipe = request.data.get('nome')
        integrantes_ids = request.data.get('integrantes') 
        if not nome_equipe or not isinstance(integrantes_ids, list):
            return Response(
                {'erro': 'O nome da equipe e uma lista de integrantes são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        alunos_da_turma_ids = set(turma.alunos_matriculados.values_list('usuario_id', flat=True))
        if not set(integrantes_ids).issubset(alunos_da_turma_ids):
            return Response(
                {'erro': 'Um ou mais alunos selecionados não pertencem a esta turma.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        nova_equipe = Equipe.objects.create(nome=nome_equipe, turma=turma)
        nova_equipe.alunos.set(integrantes_ids)
        nova_equipe.save()

        serializer = EquipeSerializer(nova_equipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_alunos_da_turma(request, turma_id):
    try:
        turma = Turma.objects.get(id=turma_id)
        alunos = turma.alunos_matriculados.select_related('usuario').all()
        
        serializer = AlunoSerializer(alunos, many=True)
        return Response(serializer.data)
        
    except Turma.DoesNotExist:
        return Response(
            {'erro': 'Turma não encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

# Views para o Sistema de Upload de Arquivos

class FileUploadView(CreateAPIView):
    """
    Endpoint para fazer upload de um novo arquivo.
    Aceita requisições multipart/form-data.
    """
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] # Habilita o parsing de arquivos

    def perform_create(self, serializer):
        """Associa o arquivo ao usuário logado antes de salvar."""
        instance = serializer.save() # O serializer já associa o usuário a partir do contexto
        logger.info(
            f"Arquivo '{instance.original_filename}' (ID: {instance.id}) "
            f"enviado por {self.request.user.username}."
        )

    def create(self, request, *args, **kwargs):
        """Garante que o contexto da requisição seja passado para o serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class FileListView(ListAPIView):
    """
    Endpoint para listar e filtrar os arquivos enviados.
    """
    serializer_class = FileListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Campos para filtragem e ordenação
    filterset_fields = ['content_type', 'category__name', 'is_public']
    search_fields = ['title', 'description', 'original_filename']
    ordering_fields = ['uploaded_at', 'file_size', 'title']
    ordering = ['-uploaded_at'] # Ordenação padrão

    def get_queryset(self):
        """
        Esta view retorna uma lista de todos os arquivos públicos
        ou os arquivos que pertencem ao usuário autenticado.
        """
        user = self.request.user
        
        # Otimiza a consulta para evitar múltiplas chamadas ao DB
        queryset = UploadedFile.objects.select_related('category', 'uploaded_by')

        # Usuários não-staff só podem ver seus próprios arquivos ou os públicos
        if not user.is_staff:
             queryset = queryset.filter(
                Q(uploaded_by=user) | Q(is_public=True)
             )
        
        return queryset.prefetch_related('tags')
