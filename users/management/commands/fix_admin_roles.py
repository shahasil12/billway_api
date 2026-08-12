from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Fixes admin roles by setting all superusers to ADMIN role'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        updated = User.objects.filter(is_superuser=True).update(role='ADMIN')
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} superusers to ADMIN role.'))
