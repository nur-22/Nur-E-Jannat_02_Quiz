from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .models import Quiz, Question, Option, Participant

from .forms import (RegisterForm, LoginForm, ParticipantForm, QuizForm, QuestionFormSet)


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful! Please login.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
            user_by_email = User.objects.filter(email__iexact=username_or_email).first()
            username = (user_by_email.username if user_by_email else username_or_email)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('dashboard')
            messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def participant_view(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)

        if form.is_valid():
            participant = form.save()
            request.session['participant_id'] = participant.id
            messages.success(request, 'Participant information saved successfully!')
            return redirect('dashboard')
    else:
        form = ParticipantForm()

    return render(request, 'participant.html', {'form': form})


@login_required
def dashboard_view(request):
    quizzes = Quiz.objects.all()
    return render(request, 'dashboard.html', {'quizzes': quizzes})


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin, login_url='login')
def quiz_editor_view(request, quiz_id=None):

    if quiz_id:
        quiz = get_object_or_404(Quiz, id=quiz_id)
    else:
        quiz = Quiz()

    if quiz.pk:
        question_queryset = Question.objects.filter(quiz=quiz).order_by('id')
    else:
        question_queryset = Question.objects.none()

    if request.method == 'POST':

        quiz_form = QuizForm(request.POST, instance=quiz)

        question_formset = QuestionFormSet(
            request.POST,
            queryset=question_queryset,
            prefix='questions'
        )

        if quiz_form.is_valid() and question_formset.is_valid():

            with transaction.atomic():

                quiz = quiz_form.save()

                # Delete selected questions.
                for form in question_formset.deleted_forms:
                    if form.instance.pk:
                        form.instance.delete()

                # Save new and edited questions.
                for form in question_formset.forms:

                    if form in question_formset.deleted_forms:
                        continue

                    if not form.has_changed():
                        continue

                    question = form.save(commit=False)
                    question.quiz = quiz
                    question.save()

                    # Delete old options.
                    question.option_set.all().delete()
                    correct_option = form.cleaned_data['correct_option']

                    # Save four new options.
                    for number in range(1, 5):

                        Option.objects.create(
                            question=question,
                            option=form.cleaned_data[f'option{number}'],
                            is_correct=(str(number) == correct_option)
                        )

            messages.success(request, 'Quiz saved successfully!')
            return redirect('dashboard')

    else:
        quiz_form = QuizForm(instance=quiz)
        question_formset = QuestionFormSet(queryset=question_queryset, prefix='questions')

    return render(request, 'quiz_editor.html',
        {'quiz_form': quiz_form, 'question_formset': question_formset, 'quiz': quiz})


@login_required
@user_passes_test(is_admin, login_url='login')
def delete_quiz_view(request, quiz_id):

    quiz = get_object_or_404(Quiz, id=quiz_id)

    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'delete_quiz.html', {'quiz': quiz})


@login_required
def take_quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = Question.objects.filter(quiz=quiz)

    # Find participant information from the session
    participant_id = request.session.get('participant_id')
    participant = Participant.objects.filter(id=participant_id).first()

    if request.method == 'POST':

        score = 0
        total = questions.count()

        for question in questions:
            selected_option_id = request.POST.get(f'question_{question.id}')

            if selected_option_id:
                option = Option.objects.filter(id=selected_option_id, question=question).first()

                if option and option.is_correct:
                    score += 1

        return render(request, 'result.html',
            {'quiz': quiz,
            'score': score,
            'total': total,
            'participant': participant,
            'participant_name': (participant.name if participant else request.user.username)}
        )

    # Randomize questions
    questions = list(questions.order_by('?'))

    # Randomize options
    question_data = []
    for question in questions:
        options = list(question.option_set.all().order_by('?'))
        question_data.append({'question': question, 'options': options})

    return render(request, 'take_quiz.html', {'quiz': quiz, 'question_data': question_data})