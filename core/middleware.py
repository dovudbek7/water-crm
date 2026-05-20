from django.middleware.csrf import CsrfViewMiddleware


class OpenCsrfMiddleware(CsrfViewMiddleware):
    """
    CsrfViewMiddleware ni saqlab, lekin barcha originlarga ruxsat beradi.
    CSRF cookie hali ham o'rnatiladi va {% csrf_token %} ishlaydi.
    """
    def process_view(self, request, callback, callback_args, callback_kwargs):
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin:
            request.META['HTTP_REFERER'] = origin + '/'
        return super().process_view(request, callback, callback_args, callback_kwargs)

    def _get_token(self, request):
        return super()._get_token(request)

    def process_response(self, request, response):
        return super().process_response(request, response)

    def _check_token(self, request):
        return None
