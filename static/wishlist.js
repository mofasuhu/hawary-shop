document.addEventListener('DOMContentLoaded', function () {
    const csrfToken = document.getElementById("csrf_token")?.value || "";

    document.querySelectorAll('.wishlist-toggle-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();

            if (this.dataset.authenticated === 'false') {
                window.location.href = '/login';
                return;
            }

            const productId = this.dataset.productId;
            const action = this.dataset.action; // 'add' or 'remove'
            const url = `/wishlist/${action}/${productId}`;
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(data.message, 'succeed');
                    
                    // If we are on the wishlist page and the action was remove, remove the card from DOM
                    if (window.location.pathname === '/wishlist' && action === 'remove') {
                        const card = this.closest('.product-card');
                        if (card) {
                            card.style.opacity = '0';
                            setTimeout(() => {
                                card.remove();
                                // Check if wishlist is empty now
                                const grid = document.getElementById('products-section');
                                if (grid && grid.querySelectorAll('.product-card').length === 0) {
                                    grid.innerHTML = `<p style="text-align: center; grid-column: 1 / -1; font-size: 18px;">${translations['Wishlist_Empty'] || 'Your wishlist is empty.'}</p>`;
                                }
                            }, 300);
                        }
                    } else {
                        // Toggle the UI for buttons on other pages
                        if (action === 'add') {
                            this.dataset.action = 'remove';
                            this.innerHTML = '<i class="fa-solid fa-heart"></i>';
                            this.style.color = 'red';
                            this.title = translations['Remove_from_Wishlist'] || 'Remove from Wishlist';
                        } else {
                            this.dataset.action = 'add';
                            this.innerHTML = '<i class="fa-regular fa-heart"></i>';
                            this.style.color = 'gray';
                            this.title = translations['Add_to_Wishlist'] || 'Add to Wishlist';
                        }
                    }
                } else {
                    showToast(data.message || 'Error updating wishlist', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error updating wishlist', 'error');
            });
        });
    });
});
