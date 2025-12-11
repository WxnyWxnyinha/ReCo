from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from usuario.models import Profile
from .forms import ProfileForm

@login_required(login_url='usuario:login')
def index(request):
    """
    Mostrar informações de perfil do usuário autenticado.
    Se o Profile não existir, cria um registro padrão.
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    context = {
        'user': request.user,
        'profile': profile,
    }
    return render(request, 'perfil/profile.html', context)

@login_required(login_url='usuario:login')
def edit_profile(request):
    """
    Editar o perfil do usuário autenticado.
    Atualiza campos do Profile e os campos básicos do User (first_name, email).
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            updated = form.save(commit=False)
            # Garantir que user_type não muda pelo POST
            if profile.user_type:
                updated.user_type = profile.user_type
            
            # Processar remoção de foto se checkbox estiver marcado
            if request.POST.get('profile_photo-clear'):
                updated.profile_photo.delete(save=False)
                updated.profile_photo = None
            
            updated.save()
            # atualizar campos simples do User
            fn = request.POST.get('first_name')
            em = request.POST.get('email')
            if fn is not None:
                request.user.first_name = fn
            if em is not None:
                request.user.email = em
            request.user.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect('perfil:index')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'perfil/edit_profile.html', {
        'form': form,
        'user': request.user,
    })

