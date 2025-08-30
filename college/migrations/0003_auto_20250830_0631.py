import os
from django.db import migrations
from django.contrib.auth import get_user_model

def create_superuser(apps, schema_editor):
    User = get_user_model()
    
    # Get credentials from environment variables
    username = os.getenv('DJANGO_SUPERUSER_USERNAME')
    password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
    email = os.getenv('DJANGO_SUPERUSER_EMAIL')

    # Create superuser only if it doesn't exist and credentials are provided
    if username and password and not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            password=password,
            email=email
        )
        print(f"Superuser '{username}' created.")

class Migration(migrations.Migration):

    dependencies = [
        ('college', '0001_initial'), # Make sure this matches your first migration file
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]