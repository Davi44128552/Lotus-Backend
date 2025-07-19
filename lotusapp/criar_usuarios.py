from core.models import Usuario, Professor, Aluno

for i in range(1, 1001):
    email = f"usuario{i}@lotus.com"
    username = f"usuario{i}"
    password = "123456"
    first_name = f"Usuário{i}"
    last_name = "Teste"
    cpf = f"{i:011d}"  # CPF com 11 dígitos

    if Usuario.objects.filter(email=email).exists():
        continue

    if i <= 450:
        tipo = Usuario.Tipo.ALUNO
    elif i <= 900:
        tipo = Usuario.Tipo.PROFESSOR
    else:
        tipo = Usuario.Tipo.ADMINISTRADOR

    usuario = Usuario.objects.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        cpf=cpf,
        tipo=tipo,
        foto_url=""
    )

    if tipo == Usuario.Tipo.ALUNO:
        Aluno.objects.create(usuario=usuario, semestre="2025.1", matricula=f"2025{i:04d}")
    elif tipo == Usuario.Tipo.PROFESSOR:
        Professor.objects.create(usuario=usuario, formacao="Mestrado", especialidade="Clínica Geral")
    elif tipo == Usuario.Tipo.ADMINISTRADOR:
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save()

print("Usuários criados com sucesso.")
