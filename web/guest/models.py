import time
from django.db import models

# Create your models here.
class GuestSession(models.Model):
    session_id = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    page_views = models.PositiveIntegerField()
    customer_id = models.CharField(max_length=10, null=True, blank=True)

    @staticmethod
    def generate_customer_id():
        import random
        import string
        timestamp = str(int(time.time()))
        random_string = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
        return f'GUEST-{timestamp}-{random_string}'
