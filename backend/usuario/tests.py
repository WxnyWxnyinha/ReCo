from django.test import TestCase
from .models import Usuario

class UsuarioModelTest(TestCase):
    def setUp(self):
        Usuario.objects.create(nome="Teste", email="teste@example.com")

    def test_usuario_criado(self):
        usuario = Usuario.objects.get(nome="Teste")
        self.assertEqual(usuario.email, "teste@example.com")