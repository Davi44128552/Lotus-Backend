import random
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker  # Importa a biblioteca Faker
from core.models import Usuario, Professor, Aluno, Turma, Equipe

class Command(BaseCommand):
    help = 'Popula o banco de dados com uma grande quantidade de dados de teste realistas.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        # --- CONFIGURAÇÕES ---
        NUM_PROFESSORES = 20
        NUM_ALUNOS = 1000
        NUM_TURMAS = 60
        SENHA_PADRAO = 'lotus123'
        
        # Instancia o Faker para gerar dados em português do Brasil
        fake = Faker('pt_BR')

        self.stdout.write(self.style.WARNING('Limpando o banco de dados...'))
        Equipe.objects.all().delete()
        Turma.objects.all().delete()
        Aluno.objects.all().delete()
        Professor.objects.all().delete()
        Usuario.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Banco de dados limpo.'))
        
        self.stdout.write(self.style.WARNING(f"Iniciando a criação de {NUM_PROFESSORES} professores..."))
        professores_criados = []
        for i in range(NUM_PROFESSORES):
            first_name = fake.first_name()
            last_name = fake.last_name()
            user = Usuario.objects.create_user(
                username=f'prof.{first_name.lower()}{i}',
                email=f'prof.{first_name.lower()}.{last_name.lower()}{i}@exemplo.com',
                password=SENHA_PADRAO,
                first_name=first_name, last_name=last_name, tipo='prof', is_active=True
            )
            prof = Professor.objects.create(usuario=user, formacao=fake.job(), especialidade="Medicina")
            professores_criados.append(prof)
        self.stdout.write(self.style.SUCCESS(f'{NUM_PROFESSORES} professores criados.'))

        self.stdout.write(self.style.WARNING(f"Iniciando a criação de {NUM_ALUNOS} alunos..."))
        alunos_criados = []
        for i in range(NUM_ALUNOS):
            first_name = fake.first_name()
            last_name = fake.last_name()
            user = Usuario.objects.create_user(
                username=f'aluno.{first_name.lower()}{i}',
                email=f'aluno.{first_name.lower()}.{last_name.lower()}{i}@exemplo.com',
                password=SENHA_PADRAO,
                first_name=first_name, last_name=last_name, tipo='alu', is_active=True
            )
            aluno = Aluno.objects.create(usuario=user, matricula=str(250000 + i), semestre=f"2025.{random.choice([1,2])}")
            alunos_criados.append(aluno)
        self.stdout.write(self.style.SUCCESS(f'{NUM_ALUNOS} alunos criados.'))

        self.stdout.write(self.style.WARNING(f"Iniciando a criação de {NUM_TURMAS} turmas e distribuindo alunos e equipes..."))
        
        # Lógica de distribuição
        alunos_por_turma = NUM_ALUNOS // NUM_TURMAS
        
        disciplinas = ["Clínica Médica", "Cardiologia", "Neurologia", "Pediatria", "Cirurgia Geral", "Ginecologia", "Dermatologia", "Ortopedia"]
        nomes_equipe = ["Curandeiros", "Alfas", "Cheettos", "Magos da Cura", "Vingadores", "Titãs", "Exploradores"]

        for i in range(NUM_TURMAS):
            # Distribui professores de forma cíclica para as turmas
            professor_responsavel = professores_criados[i % NUM_PROFESSORES]
            
            # Cria a turma com um nome de disciplina aleatório
            turma = Turma.objects.create(
                disciplina=f"{random.choice(disciplinas)} - T{i+1}",
                semestre=f"2025.{random.choice([1,2])}",
                capacidade_maxima=30,
                quantidade_alunos=0, # Será atualizado depois
                professor_responsavel=professor_responsavel
            )

            # Seleciona um "pedaço" da lista de alunos para esta turma
            start_index = i * alunos_por_turma
            end_index = start_index + alunos_por_turma
            # Garante que o último grupo pegue todos os alunos restantes
            if i == NUM_TURMAS - 1:
                end_index = NUM_ALUNOS
            
            alunos_da_turma = alunos_criados[start_index:end_index]
            turma.alunos_matriculados.set(alunos_da_turma)
            turma.quantidade_alunos = len(alunos_da_turma)
            turma.save()

            # Cria equipes dentro da turma
            # Divide os alunos da turma em equipes de ~4
            alunos_para_equipes = list(alunos_da_turma) # Cria uma cópia para embaralhar
            random.shuffle(alunos_para_equipes)
            tamanho_equipe = 4
            num_equipes = (len(alunos_para_equipes) + tamanho_equipe - 1) // tamanho_equipe # Divisão arredondada para cima

            for j in range(num_equipes):
                equipe_start = j * tamanho_equipe
                equipe_end = equipe_start + tamanho_equipe
                alunos_para_esta_equipe = alunos_para_equipes[equipe_start:equipe_end]

                if alunos_para_esta_equipe: # Garante que não criamos equipes vazias
                    equipe = Equipe.objects.create(
                        nome=f"{random.choice(nomes_equipe)} {j+1}",
                        turma=turma
                    )
                    equipe.alunos.set(alunos_para_esta_equipe)

        self.stdout.write(self.style.SUCCESS(f'{NUM_TURMAS} turmas criadas e populadas.'))
        self.stdout.write(self.style.SUCCESS('Banco de dados populado com sucesso!'))