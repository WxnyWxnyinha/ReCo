import re
from datetime import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from django.utils import timezone

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(label='Nome completo', required=True)
    phone = forms.CharField(
        label='Telefone',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': '(61) 99999-9999'})
    )
    city = forms.ChoiceField(label='Cidade', choices=Profile.CITY_CHOICES)
    user_type = forms.ChoiceField(label='Tipo de usuário', choices=Profile.USER_TYPE_CHOICES)
    cpf_cnpj = forms.CharField(label='CPF/CNPJ', required=True)
    razao_social = forms.CharField(label='Razão social', required=False)
    birth_date = forms.CharField(
        label='Data de nascimento (dd/mm/aaaa)',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'dd/mm/aaaa'})
    )
    consent_privacy = forms.BooleanField(
        label='Concordo com a Política de Privacidade e o tratamento dos meus dados (LGPD)',
        required=True,
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'phone', 'city', 'user_type', 'cpf_cnpj', 'razao_social', 'birth_date', 'consent_privacy',
            'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        select_fields = {'user_type', 'city'}
        for name, field in self.fields.items():
            if name == 'consent_privacy':
                css = 'form-check-input'
            else:
                css = 'form-select' if name in select_fields else 'form-control'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{existing} {css}".strip()

    def clean(self):
        cleaned = super().clean()
        ut = cleaned.get('user_type')
        cpf_cnpj = cleaned.get('cpf_cnpj', '') or ''
        razao = cleaned.get('razao_social')
        birth = cleaned.get('birth_date') or ''

        # Normalize digits only
        digits = re.sub(r'\D', '', cpf_cnpj)

        if ut == 'pj':
            if not digits:
                self.add_error('cpf_cnpj', 'CNPJ é obrigatório para empresas/ONGs.')
            elif len(digits) != 14:
                self.add_error('cpf_cnpj', 'CNPJ deve ter 14 dígitos.')
            if not razao:
                self.add_error('razao_social', 'Razão social é obrigatória para empresas/ONGs.')
        else:
            if not digits:
                self.add_error('cpf_cnpj', 'CPF é obrigatório para pessoa física.')
            elif len(digits) != 11:
                self.add_error('cpf_cnpj', 'CPF deve ter 11 dígitos.')
            elif razao:
                self.add_error('razao_social', 'Razão social só pode ser informada para CNPJ.')
                cleaned['razao_social'] = ''

        # Format CPF/CNPJ to standard presentation
        if digits:
            if len(digits) == 11:
                formatted = f"{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}"
            elif len(digits) == 14:
                formatted = f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"
            else:
                formatted = cpf_cnpj
            cleaned['cpf_cnpj'] = formatted

        # Validate birth_date dd/mm/yyyy
        if birth:
            try:
                dt = datetime.strptime(birth, "%d/%m/%Y").date()
                cleaned['birth_date'] = dt
            except ValueError:
                self.add_error('birth_date', 'Data deve estar no formato dd/mm/aaaa.')

        return cleaned

    def save(self, commit=True):
        user = super().save(commit)
        # Garantir permissões de admin quando tipo selecionado for administrador
        if self.cleaned_data.get('user_type') == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=['is_staff', 'is_superuser'])
        Profile.objects.update_or_create(
            user=user,
            defaults={
                'phone': self.cleaned_data.get('phone', ''),
                'city': self.cleaned_data.get('city', ''),
                'user_type': self.cleaned_data.get('user_type', 'pf'),
                'cpf_cnpj': self.cleaned_data.get('cpf_cnpj', ''),
                'razao_social': self.cleaned_data.get('razao_social', ''),
                'birth_date': self.cleaned_data.get('birth_date', None),
                'consent_privacy': self.cleaned_data.get('consent_privacy', False),
                'consent_timestamp': timezone.now(),
            }
        )
        return user