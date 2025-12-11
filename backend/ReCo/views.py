from django.shortcuts import render


def index(request):
    """Página inicial do site — renderiza templates/home.html"""
    return render(request, "home.html")


def privacy_policy(request):
    """Página de Política de Privacidade (LGPD)"""
    return render(request, "privacy.html")
