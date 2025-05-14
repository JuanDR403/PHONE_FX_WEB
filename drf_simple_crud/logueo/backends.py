from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that allows login with either username or email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Check if the input looks like an email
        is_email = '@' in username if username else False
        
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
            
        if username is None or password is None:
            return None
            
        try:
            # Try to fetch the user by username or email
            if is_email:
                # If it looks like an email, search by email
                user = User.objects.get(email=username)
            else:
                # Otherwise search by username
                user = User.objects.get(username=username)
                
            # Check the password
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
                
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            
        return None