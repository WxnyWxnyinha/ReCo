from django import forms
from .models import Donation, Message, DonationRequest

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['title', 'description', 'condition', 'city', 'contact_email', 'contact_phone', 'delivery_type', 'collection_point', 'pickup_address', 'image']
        labels = {
            'title': 'Título',
            'description': 'Descrição',
            'condition': 'Condição',
            'city': 'Cidade',
            'contact_email': 'E-mail de contato',
            'contact_phone': 'Telefone de contato',
            'delivery_type': 'Tipo de entrega',
            'collection_point': 'Ponto de coleta',
            'pickup_address': 'Endereço para retirada',
            'image': 'Imagem',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows':4, 'class':'form-control'}),
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'condition': forms.Select(attrs={'class':'form-select'}),
            'city': forms.TextInput(attrs={'class':'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class':'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class':'form-control'}),
            'delivery_type': forms.Select(attrs={'class':'form-select', 'id': 'delivery-type'}),
            'collection_point': forms.Select(attrs={'class':'form-select', 'id': 'collection-point'}),
            'pickup_address': forms.Textarea(attrs={'rows':2, 'class':'form-control', 'id': 'pickup-address'}),
            'image': forms.ClearableFileInput(attrs={'class':'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Tornar collection_point obrigatório e pickup_address opcional inicialmente
        self.fields['collection_point'].required = False
        self.fields['pickup_address'].required = False


class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ['reason']
        labels = {
            'reason': 'Por que você precisa deste item?',
        }
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Explique por que você gostaria de receber este item...',
            }),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text', 'image']
        labels = {
            'text': 'Mensagem',
            'image': 'Imagem (opcional)',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Escreva sua mensagem...',
                'id': 'message-input',
                'required': 'required'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text', '').strip()
        
        # Validar que o texto não está vazio
        if not text:
            raise forms.ValidationError('A mensagem não pode estar vazia.')
        
        return cleaned_data