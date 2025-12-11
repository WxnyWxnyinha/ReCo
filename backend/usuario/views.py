from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.conf import settings

from .forms import RegisterForm
from usuario.models import Profile


def _add_form_control_classes(form):
    for field in form.fields.values():
        existing = field.widget.attrs.get('class', '')
        field.widget.attrs['class'] = f"{existing} form-control".strip()

def index(request):
    return render(request, 'usuario/home.html', {'title': 'Usuário'})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        _add_form_control_classes(form)
        if form.is_valid():
            user = form.get_user()
            # Garantir que exista um Profile para este user
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, "Login realizado com sucesso.")
            return redirect('home')
    else:
        form = AuthenticationForm(request)
        _add_form_control_classes(form)
    return render(request, 'usuario/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu da conta.')
    return redirect('usuario:index')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Conta criada com sucesso. Faça login.")
            return redirect('usuario:login')
    else:
        form = RegisterForm()
    return render(request, 'usuario/register.html', {'form': form})


def password_reset_by_username(request):
    """Recuperar senha pelo nome de usuário ou email"""
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email', '')
        
        # Procurar por usuário usando username ou email
        try:
            user = User.objects.get(username=username_or_email)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                messages.error(request, 'Usuário ou email não encontrado.')
                return render(request, 'usuario/password_reset_by_username.html')
        
        # Gerar token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = request.build_absolute_uri(
            f'/usuario/reset/{uid}/{token}/'
        )
        
        # Enviar email
        try:
            subject = 'Recuperar Senha - ReCo'
            message = f"""Olá {user.get_full_name() or user.username},

Você solicitou uma recuperação de senha. Clique no link abaixo para definir uma nova senha:

{reset_url}

Este link é válido por 24 horas.

Se você não solicitou esta recuperação, ignore este email.

---
Equipe de Suporte
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Email de recuperação enviado com sucesso!')
            return redirect('usuario:password_reset_done')
        except Exception as e:
            messages.error(request, f'Erro ao enviar email: {str(e)}')
            return render(request, 'usuario/password_reset_by_username.html')
    
    return render(request, 'usuario/password_reset_by_username.html')


@login_required
def delete_account(request):
    """Exclusão de conta (direito ao esquecimento)"""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, 'Sua conta foi removida e seus dados pessoais foram excluídos.')
        return redirect('home')
    return render(request, 'usuario/delete_account.html')