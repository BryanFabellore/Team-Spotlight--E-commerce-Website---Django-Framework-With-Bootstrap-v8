from django.utils import timezone
from guest.models import GuestSession
from customer.models import Customer  # Import the Customer model from the customer app

class GuestSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        customer_id = None  # Initialize customer_id as None
        customer_username = ""  # Initialize customer_username with an empty string

        if hasattr(request, 'user') and request.user.is_authenticated:
            # User is authenticated (customer)
            customer_id = request.user.customer.id
            customer_username = request.user.customer.username
        else:
            # User is a guest
            session_id = request.session.session_key
            if not session_id:
                request.session.save()  # Generate a session key
                session_id = request.session.session_key
                guest_session = GuestSession.objects.create(session_id=session_id, start_time=timezone.now(), end_time=timezone.now(), page_views=0)

                # Create a customer ID for the guest
                guest_session.customer_id = GuestSession.generate_customer_id()
                guest_session.save()

                customer_id = guest_session.customer_id
                customer_username = "Guest"

        # Pass the customer ID and username to the request for use in views
        request.customer_id = customer_id
        request.customer_username = customer_username

        response = self.get_response(request)

        return response
