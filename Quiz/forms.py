from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory

from .models import Quiz, Question, Participant

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(forms.Form):
    username_or_email = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'class_name', 'age', 'gender', 'institution']
        widgets = {
            'gender': forms.Select(
                choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
                )
            }


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description']


class QuestionEditorForm(forms.ModelForm):

    option1 = forms.CharField(max_length=200, required=False, label="Option 1")
    option2 = forms.CharField(max_length=200, required=False, label="Option 2")
    option3 = forms.CharField(max_length=200, required=False, label="Option 3")
    option4 = forms.CharField(max_length=200, required=False, label="Option 4")

    correct_option = forms.ChoiceField(
        choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3'), ('4', 'Option 4')],
        required=False,
        label="Correct Answer"
    )

    class Meta:
        model = Question
        fields = ['question']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            options = list(self.instance.option_set.order_by('id'))

            for index, option in enumerate(options[:4], start=1):
                self.initial[f'option{index}'] = option.option

                if option.is_correct:
                    self.initial['correct_option'] = str(index)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('DELETE'):
            return cleaned_data
        question = cleaned_data.get('question')

        options = [
            cleaned_data.get('option1'),
            cleaned_data.get('option2'),
            cleaned_data.get('option3'),
            cleaned_data.get('option4')
        ]

        correct_option = cleaned_data.get('correct_option')

        if not question and not any(options) and not correct_option:
            return cleaned_data

        if not question:
            self.add_error('question', 'Please enter the question.')

        for index, option in enumerate(options, start=1):
            if not option:
                self.add_error(f'option{index}', 'Please enter this option.')

        if not correct_option:
            self.add_error('correct_option', 'Please select the correct answer.')

        return cleaned_data

QuestionFormSet = modelformset_factory(Question, form=QuestionEditorForm, extra=0, can_delete=True)