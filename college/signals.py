from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Faculty

@receiver(post_save, sender=Faculty)
def make_faculty_staff(sender, instance, created, **kwargs):
    """
    Automatically make a User a staff member when a Faculty profile is created for them.
    """
    if created:
        user = instance.user
        user.is_staff = True
        user.save()