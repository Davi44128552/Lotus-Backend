import json

from django.contrib.auth import authenticate
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Aluno, CasoClinico, Diagnostico, Professor, Turma, Usuario
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import TurmaSerializer

@csrf_exempt
@require_http_methods(['POST'])
def cadastro(request):
    try:
        data = json.loads(request.body)

        # dados recebidos do post
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

        # Verificar se o usuário (email ou username ou cpf) já existe
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

        # Perfil de aluno
        if tipo_usuario_str == Usuario.Tipo.ALUNO.value:
            novo_usuario_obj.tipo = Usuario.Tipo.ALUNO
            novo_usuario_obj.save()
            Aluno.objects.create(
                usuario=novo_usuario_obj,
                semestre=data.get('semestre', 'N/A'),
                ira=data.get('ira', 0.0),
            )
        # Perfil de professor
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
            novo_usuario_obj.is_superuser = data.get(
                'is_superuser', False
            )  # Para criar admins sem permissões de superusuário
            novo_usuario_obj.save()
        else:
            # Caso não cosniga achar o tipo eu deleto o usuario criado
            novo_usuario_obj.delete()
            return JsonResponse({'erro': 'Tipo de usuário inválido fornecido.'}, status=400)

        return JsonResponse(
            {
                'mensagem': 'Usuário cadastrado com sucesso!',
                'usuario': {
                    'id': novo_usuario_obj.id,
                    'first_name': novo_usuario_obj.first_name,
                    'email': novo_usuario_obj.email,
                    'username': novo_usuario_obj.username,
                },
            },
            status=201,
        )

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
        return Response(
            {'erro': 'Email e senha são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    usuario = authenticate(request, username=email, password=senha_fornecida)

    if usuario is not None:
        refresh = RefreshToken.for_user(usuario)

        user_data_response = {
            'id': usuario.id,
            'first_name': usuario.first_name,
            'last_name': usuario.last_name,
            'email': usuario.email,
            'username': usuario.username,
            'tipo': usuario.tipo,
        }

        return Response(
            {
                'mensagem': 'Login bem-sucedido!',
                'usuario': user_data_response,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {'erro': 'Credenciais inválidas.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
# Funções para professores

# Criando uma função para retornar as informações do professor em uma rota


@require_http_methods(['GET'])
def info_perfil_prof(request, id):
    try:
        professor = Professor.objects.get(usuario_id=id)
        dados = {
            'nome': f'{professor.usuario.first_name} {professor.usuario.last_name}',
            'email': professor.usuario.email,
            'formacao': professor.formacao,
            'especialidade': professor.especialidade,
        }

        return JsonResponse(dados)

    except Professor.DoesNotExist:
        raise Http404('Professor não encontrado.')

    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)


# Função para listar as turmas do professor
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_turmas_prof(request, id):
    try:
        professor_profile = request.user.professor
        turmas = Turma.objects.filter(professor_responsavel=professor_profile)

        turmas_professor = []
        for turma in turmas:
            turmas_professor.append(
                {'id': turma.id, 'disciplina': turma.disciplina, 'semestre': turma.semestre}
            )

        return Response(turmas_professor)

    except Professor.DoesNotExist:
        return Response(
            {'erro': 'Perfil de professor não encontrado para este usuário.'},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {'erro': f'Ocorreu um erro inesperado: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
# Função para mostrar os casos do professor
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


# Funções para casos
# Função para expor detalhes dos casos
@require_http_methods(['GET'])
def info_casos(request, prof_id, caso_id):
    try:
        caso = CasoClinico.objects.get(id=caso_id)
        diagnostico = Diagnostico.objects.get(caso_clinico=caso)
        dados = {
            'id': caso.id,
            'título': caso.titulo,
            'descrição': caso.descricao,
            'area': caso.area,
            'arquivos': caso.arquivos,
            'dificuldade': caso.dificuldade,
            'diagnóstico': diagnostico.descricao,
        }

        return JsonResponse(dados)

    except Professor.DoesNotExist:
        raise Http404('Professor não encontrado.')

    except CasoClinico.DoesNotExist:
        raise Http404('Caso clínico não encontrado.')

    except Exception as e:
        return JsonResponse({'erro': f'Ocorreu um erro inesperado: {str(e)}'}, status=500)


# Funções para turmas
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def info_turmas(request, id):
    try:
        turma = Turma.objects.select_related('professor_responsavel__usuario').prefetch_related('alunos_matriculados__usuario').get(id=id)
        serializer = TurmaSerializer(turma)
        return Response(serializer.data)

    except Turma.DoesNotExist:
        return Response(
            {'erro': 'Turma não encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )