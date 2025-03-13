from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from wsapp.models import UserProfile

class UserRegistrationForm(UserCreationForm):
    # Add custom fields for the UserProfile model
    profile_picture = forms.ImageField(required=False, label="Profile Picture")
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        required=False, 
        label="Bio"
    )
    # isonline = forms.BooleanField(initial=False, required=False, label="Online Status")

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email']

    def save(self, commit=True):
        # Save the user first
        user = super().save(commit=False)

        if commit:
            user.save()

        # Save the UserProfile details
        user_profile = UserProfile.objects.create(
            user=user,
            profile_picture=self.cleaned_data['profile_picture'],
            bio=self.cleaned_data['bio'],
        )

        return user

