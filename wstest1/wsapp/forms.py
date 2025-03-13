# forms.py
from django import forms
from .models import Room

from django.contrib.auth.models import User

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'logo', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

class UserRoomForm(forms.Form):
    room_id = forms.ModelChoiceField(queryset=Room.objects.all(), label="Select Room", widget=forms.Select(attrs={'class': 'form-control'}))
    
    # Multiple user selection, no Select2 dependency
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.exclude(username='admin'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),  # Use a regular select box
        required=False
    )
    
    operation = forms.ChoiceField(
        choices=[('add', 'Add Users'), ('remove', 'Remove Users')],
        label="Operation",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class RemoveUserForm(forms.Form):
    username = forms.CharField(max_length=150, label="Username", widget=forms.TextInput(attrs={'class': 'form-control'}))