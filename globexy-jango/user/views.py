from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout, \
    update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import deprecate_current_app
from django.http.response import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from user import thread_local, redis_tokens_get, redis_tokens_set, redis_tokens_delete, \
    generate_tokens_key
import user
from user.forms import RegistrationForm
from user.models import User
from user.utils import as_register, as_confirm, as_logout, as_change_password


@deprecate_current_app
@sensitive_post_parameters()
@never_cache
def login(
        request,
        redirect_field_name=REDIRECT_FIELD_NAME,
        authentication_form=AuthenticationForm,
        extra_context=None,
        redirect_authenticated_user=False
):
    """
    Displays the login form and handles the login action.
    """

    if request.user.is_authenticated:
        return JsonResponse({'status': 'fail', 'errors': 'Already authenticated'})

    if request.method == "GET":
        logout(request)
        return JsonResponse({'status': 'fail', 'errors': 'Empty form'})

    form = authentication_form(request, data=request.POST)
    if form.is_valid():
        auth_login(request, form.get_user())
        if hasattr(form.get_user(), 'auth_tokens'):
            # Логиним авторизованного пользователя
            tokens_key = generate_tokens_key()
            redis_tokens_set(tokens_key, form.get_user().auth_tokens)
            thread_local.tokens_key = tokens_key

        if not request.POST.get('remember', False):
            request.session.set_expiry(0)

        return JsonResponse({'status': 'success'})

    logout(request)
    return JsonResponse({'status': 'fail', 'errors': dict(form.errors)})


@never_cache
@sensitive_post_parameters('password1', 'password2')
def register(request):

    if request.method != 'POST':
        return JsonResponse({'status': 'fail', 'errors': 'Empty form'})

    form = RegistrationForm(request.POST)

    # If the form is valid, try to register the user on the Auth-server
    if form.is_valid():
        result, error = as_register(
            request,
            form.cleaned_data['username'],
            form.cleaned_data['email'],
            form.cleaned_data['password']
        )

        if error:
            form.add_error('username', error['message'])
            print(result,error)

    # If the form is still valid, complete the user registration.
    if not form.is_valid():
        # The form is not valid.
        return JsonResponse({'status': 'fail', 'errors': dict(form.errors)})

    # user = User.objects.create_user(
    #     username=form.cleaned_data['username'],
    #     password=form.cleaned_data['password'],
    #     email=form.cleaned_data['email'],
    #     as_user_id=result['user_id']
    # )
    # user.password = None
    # user.save()

    return JsonResponse({'status': 'success'})

@sensitive_post_parameters()
def confirm(request):
    #print(request.POST.get('email'),request.POST.get('regkey'))
    key = request.POST.get('email')
    mail = request.POST.get('regkey')
    result, error = as_confirm(request)
    
    if error: return JsonResponse({'status':error['message']}) 
    return JsonResponse({'status':result})
    
def logout_page(request):
    if not hasattr(thread_local, 'tokens_key'):
        logout(request)
        return JsonResponse({'status': 'success'})

    tokens = redis_tokens_get(thread_local.tokens_key)
    if tokens:
        result, errors = as_logout(tokens)
        if errors:
            return JsonResponse({'status': 'fail', 'errors': errors['message']})

    redis_tokens_delete(thread_local.tokens_key)
    del(thread_local.tokens_key)
    logout(request)
    return JsonResponse({'status': 'success'})


def status(request):
    if request.user.is_anonymous():
        user = {
            'authenticated': False,
            'user': {
                'as_user_id': None,
                'username': '',
                'email': None,
                'phone': None,
                'first_name': None,
                'last_name': None
            }
        }
    else:
        user = {
            'authenticated': True,
            'user': {
                'as_user_id': request.user.as_user_id,
                'username': request.user.username,
                'email': request.user.email,
                'phone': request.user.phone,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
        }

    return JsonResponse(user)


@sensitive_post_parameters()
@login_required
@deprecate_current_app
def change_password(request):
    if request.method != "POST":
        return JsonResponse({'status': 'fail', 'errors': 'Empty form'})

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            tokens = redis_tokens_get(thread_local.tokens_key)
            result, error = as_change_password(
                tokens,
                {
                    'old_pass': form.cleaned_data['old_password'],
                    'new_pass': form.cleaned_data['new_pass']
                }
            )
            if error:
                return JsonResponse({'status': 'fail', 'errors': error['message']})

            update_session_auth_hash(request, form.user)
            return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'fail'})
