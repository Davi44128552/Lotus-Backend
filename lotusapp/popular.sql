DELETE FROM core_equipe_alunos;
DELETE FROM core_turma_alunos_matriculados;
DELETE FROM core_equipe;
DELETE FROM core_turma;
DELETE FROM core_aluno;
DELETE FROM core_professor;
DELETE FROM core_usuario;


-- 1. Inserindo Usuários (Professores e Alunos) - VERSÃO CORRIGIDA
-- A senha para TODOS os usuários é 'lotus123'
-- Os campos booleanos agora usam 1 para True e 0 para False.
INSERT INTO core_usuario (id, password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, tipo, cpf, foto_url) VALUES
(1, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'prof.helena', 'Helena', 'Ramos', 'helena.ramos@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'prof', '11122233344', ''),
(2, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'prof.carlos', 'Carlos', 'Braga', 'carlos.braga@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'prof', '22233344455', ''),
(101, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'ana.silva', 'Ana', 'Silva', 'ana.silva@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'alu', '10110110101', ''),
(102, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'bruno.costa', 'Bruno', 'Costa', 'bruno.costa@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'alu', '10210210202', ''),
(103, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'carla.dias', 'Carla', 'Dias', 'carla.dias@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'alu', '10310310303', ''),
(104, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'diogo.lima', 'Diogo', 'Lima', 'diogo.lima@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'alu', '10410410404', ''),
(105, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'elisa.santos', 'Elisa', 'Santos', 'elisa.santos@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'alu', '10510510505', ''),
(106, 'pbkdf2_sha256$720000$P9qL7pD8iE0rJ1f4a5t6$VwGbtfN2XG1bZpYy+lT3dF8eR7cK6oH5aV3iM9kE0o=', 0, 'felipe.melo', 'Felipe', 'Melo', 'felipe.melo@exemplo.com', 0, 1, '2025-07-06 20:00:00', 'alu', '10610610606', '');


-- 2. Inserindo Perfis de Professor
-- A chave primária (usuario_id) corresponde ao ID do usuário criado acima.
INSERT INTO core_professor (usuario_id, formacao, especialidade) VALUES
(1, 'Doutorado em Medicina', 'Cardiologia'),
(2, 'Mestrado em Ciências da Saúde', 'Neurologia');


-- 3. Inserindo Perfis de Aluno
-- A chave primária (usuario_id) corresponde ao ID do usuário criado acima.
INSERT INTO core_aluno (usuario_id, semestre, matricula) VALUES
(101, '2025.1', '251001'),
(102, '2025.1', '251002'),
(103, '2025.1', '251003'),
(104, '2025.2', '252004'),
(105, '2025.2', '252005'),
(106, '2025.2', '252006');


-- 4. Inserindo Turmas
-- Cada turma é associada a um professor (professor_responsavel_id).
INSERT INTO core_turma (id, disciplina, semestre, capacidade_maxima, quantidade_alunos, professor_responsavel_id) VALUES
(1, 'Clínica Médica I', '2025.1', 30, 3, 1),
(2, 'Bases Neurológicas', '2025.2', 25, 3, 2);


-- 5. Matriculando Alunos nas Turmas (Tabela de Junção Many-to-Many)
INSERT INTO core_turma_alunos_matriculados (turma_id, aluno_id) VALUES
(1, 101), (1, 102), (1, 103), -- Alunos 101, 102, 103 na Turma 1
(2, 104), (2, 105), (2, 106);  -- Alunos 104, 105, 106 na Turma 2


-- 6. Inserindo Equipes dentro das Turmas
INSERT INTO core_equipe (id, nome, turma_id) VALUES
(1, 'Curandeiros', 1),
(2, 'Cheettos', 1),
(3, 'Alfas', 2),
(4, 'Magos da Cura', 2);


-- 7. Adicionando Alunos às Equipes (Tabela de Junção Many-to-Many)
INSERT INTO core_equipe_alunos (equipe_id, aluno_id) VALUES
(1, 101), (1, 102), -- Equipe 1 com alunos 101 e 102
(2, 103),          -- Equipe 2 com aluno 103
(3, 104), (3, 105), -- Equipe 3 com alunos 104 e 105
(4, 106);          -- Equipe 4 com aluno 106