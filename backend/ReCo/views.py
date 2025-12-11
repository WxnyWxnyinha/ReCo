from django.shortcuts import render


def index(request):
    """Página inicial do site — renderiza templates/home.html"""
    return render(request, "home.html")


def privacy_policy(request):
    """Página de Política de Privacidade (LGPD)"""
    return render(request, "privacy.html")


def ping(request):
    """Healthcheck simples para testar conectividade."""
    from django.http import HttpResponse
    return HttpResponse("ok", content_type="text/plain")
