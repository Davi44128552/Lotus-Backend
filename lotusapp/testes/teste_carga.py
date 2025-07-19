from locust import HttpUser, TaskSet, task, between
import random
import string

usuarios_teste = [
    {"email": f"usuario{i}@lotus.com", "senha": "123456"}
    for i in range(1, 101)
]

# IDs que você pode ter que ajustar com base no seu banco de dados
TURMA_ID = 1
CASO_ID = 1

class TarefasDoUsuario(TaskSet):
    def on_start(self):
        self.usuario = random.choice(usuarios_teste)
        self.token = None
        self.headers = {}
        self.tipo = None
        self.user_id = None
        self.login()

    def login(self):
        response = self.client.post(
            "/auth/login/",
            json={
                "email": self.usuario["email"],
                "senha": self.usuario["senha"]
            }
        )
        if response.status_code == 200:
            dados = response.json()
            self.token = dados.get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.tipo = dados.get("usuario", {}).get("tipo")
            self.user_id = dados.get("usuario", {}).get("id")
        else:
            print(f"Erro ao fazer login com {self.usuario['email']}: {response.text}")

    @task(2)
    def obter_perfil_professor(self):
        if self.tipo == "prof" and self.user_id:
            self.client.get(f"/auth/professores/{self.user_id}/", headers=self.headers)

    @task(1)
    def listar_turmas(self):
        if self.tipo == "prof" and self.user_id:
            self.client.get(f"/auth/professores/{self.user_id}/turmas", headers=self.headers)

    @task(1)
    def listar_casos(self):
        if self.tipo == "prof" and self.user_id:
            self.client.get(f"/auth/professores/{self.user_id}/casos", headers=self.headers)

    @task(1)
    def listar_equipes_turma_id1(self):
        if self.token:
            self.client.get(f"/auth/turmas/{TURMA_ID}/equipes", headers=self.headers)

class UsuarioSimulado(HttpUser):
    tasks = [TarefasDoUsuario]
    wait_time = between(1, 3)
    host = "http://localhost:8000"
