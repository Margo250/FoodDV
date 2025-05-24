// Функция для отправки AJAX-запросов
async function sendCartRequest(url, method = 'POST', data = {}) {
    const response = await fetch(url, {
        method: method,
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Обновление счетчика
function updateCartCounter(count) {
    const counter = document.getElementById('cart-counter');
    if (counter) {
        counter.textContent = count;
        counter.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    const cart = JSON.parse('{{ request.session.cart|default:"{}"|escapejs }}');
    updateCartCounter(Object.keys(cart).length);
});

// После успешного добавления/удаления товара
const event = new Event('cartUpdated');
document.dispatchEvent(event);
