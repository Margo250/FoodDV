# middleware.py
class CartMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Гарантируем что корзина - это словарь
        if not isinstance(request.session.get('cart'), dict):
            request.session['cart'] = {}
            request.session.modified = True
        
        response = self.get_response(request)
        
        # После обработки запроса проверяем еще раз
        if hasattr(request, 'session') and 'cart' in request.session:
            if not isinstance(request.session['cart'], dict):
                request.session['cart'] = {}
                request.session.modified = True
        
        return response
