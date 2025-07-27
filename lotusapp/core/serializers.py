import hashlib # Adicionado para cálculo de hash
from rest_framework import serializers

# --- Imports Atualizados ---
# Adicionados UploadedFile, Category, Tag para o sistema de upload
from .models import (
    Alternativa,
    ComponenteNotaComposta,
    Exame,
    NotaAvaliacao,
    NotaComposta,
    Questao,
    Resposta,
    ResultadoNotaComposta,
    Turma,
    Aluno,
    Professor,
    Equipe,
    UploadedFile,
    Category,
    Tag,
)
# Adicionado o validador customizado que criamos
from .validators import validate_file_type

class AlternativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alternativa
        fields = ['id', 'texto', 'correta', 'pontuacao']

class QuestaoSerializer(serializers.ModelSerializer):
    alternativas = AlternativaSerializer(many=True, read_only=True)

    class Meta:
        model = Questao
        fields = ['id', 'enunciado', 'tipo', 'valor_total', 'resposta_modelo', 'alternativas']

class ExameSerializer(serializers.ModelSerializer):
    questoes = QuestaoSerializer(many=True, read_only=True)
    estado = serializers.CharField(source='estado', read_only=True)

    class Meta:
        model = Exame
        fields = [
            'id',
            'turma',
            'tipo',
            'fase',
            'titulo',
            'descricao',
            'deadline',
            'data_liberacao',
            'fator_penalidade',
            'estado',
            'questoes',
        ]
        read_only_fields = ['data_liberacao', 'estado']

class RespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = ['id', 'questao', 'alternativa', 'resposta_texto', 'data_resposta']
        extra_kwargs = {
            'questao': {'required': True},
        }

class CorrecaoRespostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resposta
        fields = ['id', 'pontuacao_obtida', 'comentario_correcao', 'corrigida']

class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaAvaliacao
        fields = ['id', 'exame', 'tipo', 'valor', 'data_criacao']

class ComponenteNotaCompostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponenteNotaComposta
        fields = ['id', 'exame', 'peso']

class NotaCompostaSerializer(serializers.ModelSerializer):
    componentes = ComponenteNotaCompostaSerializer(many=True)

    class Meta:
        model = NotaComposta
        fields = ['id', 'nome', 'turma', 'componentes']

    def create(self, validated_data):
        componentes_data = validated_data.pop('componentes')
        nota_composta = NotaComposta.objects.create(**validated_data)

        for componente_data in componentes_data:
            ComponenteNotaComposta.objects.create(nota_composta=nota_composta, **componente_data)

        return nota_composta

class ResultadoNotaCompostaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoNotaComposta
        fields = ['id', 'nota_composta', 'valor', 'data_calculo']

class AlunoTurmaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='usuario.id', read_only=True)
    nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'matricula']

class AlunoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='usuario.id', read_only=True)
    nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'email', 'matricula']

class TurmaSerializer(serializers.ModelSerializer):
    professor = serializers.StringRelatedField(source='professor_responsavel.usuario.get_full_name')
    alunos = AlunoSerializer(many=True, read_only=True, source='alunos_matriculados')

    class Meta:
        model = Turma
        fields = ['id', 'disciplina', 'semestre', 'capacidade_maxima', 'quantidade_alunos', 'professor', 'alunos']


class AlunoTurmaSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='usuario.id', read_only=True)
    nome = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'matricula']

class IntegranteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='usuario.id', read_only=True)
    nome = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'matricula']
        
class EquipeSerializer(serializers.ModelSerializer):
    integrantes = IntegranteSerializer(many=True, source='alunos')
    
    class Meta:
        model = Equipe
        fields = ['id', 'nome', 'integrantes']
        
        
        


# Serializers para o Sistema de Upload de Arquivos
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']

class FileUploadSerializer(serializers.ModelSerializer):
    # Campo para receber o arquivo, write_only=True significa que ele é usado para upload, mas não é exibido na resposta
    # O validador customizado é aplicado aqui para garantir a segurança no nível da API
    file = serializers.FileField(write_only=True, validators=[validate_file_type])
    
    # Campo para exibir a URL completa do arquivo na resposta da API
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UploadedFile
        fields = [
            'id', 'file', 'original_filename', 'title', 'description', 'tags',
            'category', 'file_size', 'content_type', 'file_url', 'uploaded_at',
            'is_public'
        ]
        # Campos que são preenchidos pelo sistema, não pelo usuário
        read_only_fields = [
            'id', 'original_filename', 'file_size', 'content_type', 
            'file_url', 'uploaded_at', 'file_hash', 'uploaded_by'
        ]

    def get_file_url(self, obj):
        """Retorna a URL absoluta do arquivo para ser consumida pelo frontend."""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def create(self, validated_data):
        """
        Sobrescreve o método create para lidar corretamente com o arquivo
        e com a relação ManyToManyField 'tags'.
        """
        # 1. Separa as tags e o arquivo do resto dos dados
        tags_data = validated_data.pop('tags', None)
        file_obj = validated_data.pop('file')
        user = self.context['request'].user

        # 2. Preenche o resto dos metadados
        validated_data['uploaded_by'] = user
        validated_data['original_filename'] = file_obj.name
        validated_data['file_size'] = file_obj.size
        validated_data['content_type'] = file_obj.content_type

        # 3. Calcula o hash
        file_hash = hashlib.sha256()
        for chunk in file_obj.chunks():
            file_hash.update(chunk)
        validated_data['file_hash'] = file_hash.hexdigest()
        
        # Opcional: Verifica se o hash já existe
        if UploadedFile.objects.filter(file_hash=validated_data['file_hash']).exists():
            raise serializers.ValidationError({"detail": "Este arquivo já foi enviado anteriormente."})

        # 4. Cria o objeto UploadedFile principal (sem as tags)
        instance = UploadedFile.objects.create(**validated_data)
        
        # 5. Salva o arquivo físico associado à instância
        instance.file.save(file_obj.name, file_obj)

        # 6. Se houver tags, as adiciona à instância já criada
        if tags_data is not None:
            instance.tags.set(tags_data)

        # 7. Retorna a instância completa
        return instance

class FileListSerializer(serializers.ModelSerializer):
    """
    Serializer otimizado para listagens, exibindo apenas os campos essenciais
    para melhorar a performance.
    """
    file_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = UploadedFile
        fields = [
            'id', 'title', 'original_filename', 'file_size', 
            'content_type', 'uploaded_at', 'is_public', 'file_url'
        ]
        
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

