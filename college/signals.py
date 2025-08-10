from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Faculty

@receiver(post_save, sender=Faculty)
def make_faculty_staff(sender, instance, created, **kwargs):
    """
    Automatically make a User a staff member when a Faculty profile is created for them.
    """
    # 'created' is a boolean that is True only the first time the object is saved
    if created:
        # 'instance' is the Faculty object that was just saved.
        # Its 'faculty_id' field is the User object itself.
        user = instance.user
        user.is_staff = True
        user.save()