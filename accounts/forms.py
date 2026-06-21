from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, Education, Certificate, Activity, Project

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = '사용자 이름을 입력해주세요.'
        self.fields['email'].help_text = '연락 가능한 이메일 주소를 입력해주세요.'
        self.fields['password1'].help_text = '비밀번호는 최소 8자 이상이어야 합니다.'
        self.fields['password2'].label = '비밀번호 확인'
        self.fields['password2'].help_text = '비밀번호를 다시 한번 입력해주세요.'

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'skills']
        widgets = {
            'skills': forms.CheckboxSelectMultiple,
        }


class EducationForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d']
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d'],
        required=False
    )
    class Meta:
        model = Education
        exclude = ['user']

class CertificateForm(forms.ModelForm):
    date_acquired = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d']
    )
    class Meta:
        model = Certificate
        exclude = ['user']

class ActivityForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d']
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d'],
        required=False
    )
    class Meta:
        model = Activity
        exclude = ['user']

class ProjectForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d']
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        input_formats=['%Y-%m-%d', '%Y/%m/%d'],
        required=False
    )
    class Meta:
        model = Project
        exclude = ['user']
