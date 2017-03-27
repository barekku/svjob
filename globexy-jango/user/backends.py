from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from user import thread_local, redis_tokens_get
from user.utils import as_authenticate, as_logout, as_user_profile, as_login


class PhoneBackend(ModelBackend):
    '''Authentication by phone number'''

    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user


class AuthServerBackend(ModelBackend):
    """
    This backend is to be used in conjunction with the ``RemoteUserMiddleware``
    found in the middleware module of this package, and is used when the server
    is handling authentication outside of Django.

    By default, the ``authenticate`` method creates ``User`` objects for
    usernames that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """

    # Create a User object if not already in the database?
    create_unknown_user = True

    def authenticate(self, username=None, password=None, **kwargs):
        if not username or not password:
            return

        user = None
        username = self.clean_username(username)

        if hasattr(thread_local, 'tokens_key') and thread_local.tokens_key is not None:
            tokens = redis_tokens_get(thread_local.tokens_key)
            as_logout(tokens)

        self.tokens, error = as_login(username, password)
        if error:
            return None

        UserModel = get_user_model()

        # Note that this could be accomplished in one try-except clause, but
        # instead we use get_or_create when creating unknown users since it has
        # built-in safeguards for multiple threads.
        if self.create_unknown_user:
            user, created = UserModel._default_manager.get_or_create(**{
                UserModel.USERNAME_FIELD: username
            })
            if created or user.as_user_id is None:
                user = self.configure_user(user)
        else:
            try:
                user = UserModel._default_manager.get_by_natural_key(username)
            except UserModel.DoesNotExist:
                pass

        user.auth_tokens = self.tokens
        return user if self.user_can_authenticate(user) else None

    def clean_username(self, username):
        """
        Performs any cleaning on the "username" prior to using it to get or
        create the user object.  Returns the cleaned username.

        By default, returns the username unchanged.
        """
        return username

    def configure_user(self, user):
        """
        Configures a user after creation and returns the updated user.

        By default, returns the user unmodified.
        """
        result, error = as_authenticate(self.tokens)
        if result:
            user.as_user_id = result['user_id']

        result, error = as_user_profile(self.tokens)
        if result:
            user.email = result['email']

        user.save()

        return user
