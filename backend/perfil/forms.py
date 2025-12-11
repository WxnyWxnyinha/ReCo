from datetime import datetime

from django import forms

from usuario.models import Profile

class ProfileForm(forms.ModelForm):
    birth_date = forms.CharField(
        required=False,
        label='Data de Nascimento',
        widget=forms.TextInput(attrs={'placeholder': 'dd/mm/aaaa', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.birth_date:
            self.initial['birth_date'] = self.instance.birth_date.strftime('%d/%m/%Y')
        if self.instance and self.instance.user_type:
            # Evita alteração do tipo de usuário após cadastro
            self.fields['user_type'].disabled = True
            self.fields['user_type'].widget.attrs['aria-readonly'] = 'true'
        if self.instance and self.instance.cpf_cnpj:
            # Bloqueia edição do documento após cadastro
            self.fields['cpf_cnpj'].disabled = True
            self.fields['cpf_cnpj'].widget.attrs.update({'aria-readonly': 'true', 'placeholder': ''})
            
            # Se o documento é CPF (11 dígitos), bloqueia razão social
            digits = ''.join(ch for ch in self.instance.cpf_cnpj if ch.isdigit())
            if len(digits) == 11:
                # É CPF - razão social deve ficar travada
                self.fields['razao_social'].disabled = True
                self.fields['razao_social'].widget.attrs['aria-readonly'] = 'true'
                self.fields['razao_social'].help_text = 'Razão social é apenas para Empresas/ONGs.'

    class Meta:
        model = Profile
        fields = ['phone', 'city', 'user_type', 'cpf_cnpj', 'razao_social', 'birth_date', 'profile_photo']
        widgets = {
            'user_type': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'cpf_cnpj': forms.TextInput(attrs={'placeholder': 'CPF ou CNPJ', 'class': 'form-control'}),
            'razao_social': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': '(61) 99999-9999', 'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'profile_photo': 'Foto do perfil',
        }

    def clean_birth_date(self):
        value = self.cleaned_data.get('birth_date')
        if not value:
            return None
        try:
            return datetime.strptime(value, '%d/%m/%Y').date()
        except ValueError as exc:
            raise forms.ValidationError('Use o formato dd/mm/aaaa.') from exc

    def clean(self):
        cleaned = super().clean()
        cpf_cnpj = cleaned.get('cpf_cnpj') or ''
        razao = cleaned.get('razao_social') or ''

        # Se já existe documento salvo, preserva valor original (mesmo que o campo venha vazio por estar disabled)
        if self.instance and self.instance.cpf_cnpj:
            cleaned['cpf_cnpj'] = self.instance.cpf_cnpj

        digits = ''.join(ch for ch in cpf_cnpj if ch.isdigit())

        if digits and len(digits) == 11 and razao:
            self.add_error('razao_social', 'Razão social só pode ser informada para CNPJ.')
            cleaned['razao_social'] = ''

        return cleaned

    def clean_user_type(self):
        # Mantém o tipo original, impedindo mudança pelo form
        if self.instance and self.instance.user_type:
            return self.instance.user_type
        return self.cleaned_data.get('user_type')