from rest_framework import serializers

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
)


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