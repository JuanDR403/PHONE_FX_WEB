from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    """
    Model for storing user profile information including profile photo.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create or update user profile when user is created or updated
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Create a Profile for a new User instance or update the Profile for an existing User instance.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        # Make sure the profile exists
        Profile.objects.get_or_create(user=instance)