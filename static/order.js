const csrfToken = document.getElementById("csrf_token")?.value || "";

document.addEventListener('DOMContentLoaded', function () {
    reapplyEventListeners();  // This will ensure listeners are applied when the page loads
});

function reapplyEventListeners() {
    const addToCartButton = document.getElementById('add-to-cart-button');
    if (addToCartButton) {
        // Clone the node to remove any previous listeners before adding a new one
        const newButton = addToCartButton.cloneNode(true);
        addToCartButton.parentNode.replaceChild(newButton, addToCartButton);

        newButton.addEventListener('click', function () {
            if (this.dataset.authenticated === 'false') {
                window.location.href = '/login';
                return;
            }
            // Call our new handler function
            handleUpdateCartQuantity();
        });
    }

    document.querySelectorAll('.ordercard-plus-button').forEach(function (button) {
        if (button) {  // Ensure the button exists
            button.replaceWith(button.cloneNode(true));
        } 
    });
    document.querySelectorAll('.ordercard-minus-button').forEach(function (button) {
        if (button) {  // Ensure the button exists
            button.replaceWith(button.cloneNode(true));
        } 
    });



    document.querySelectorAll('.remove-item-button').forEach(function (button) {
        if (button) {
            button.replaceWith(button.cloneNode(true));
        }
    });


    // Reapply event listeners for order plus and minus buttons
    document.querySelectorAll('.ordercard-plus-button').forEach(function (button) {
        if (button) {  // Ensure the button exists
            button.addEventListener('click', function () {
                var cartKey = this.getAttribute('data-cart-key'); // Changed to data-cart-key
                ordercardPlusButton(cartKey); // Pass cart_key
            });
        } 
    });

    document.querySelectorAll('.ordercard-minus-button').forEach(function (button) {
        if (button) {  // Ensure the button exists
            button.addEventListener('click', function () {
                var cartKey = this.getAttribute('data-cart-key'); // Changed to data-cart-key
                ordercardMinusButton(cartKey); // Pass cart_key
            });
        } 
    });




    document.querySelectorAll('.remove-item-button').forEach(function (button) {
        if (button) {
            button.addEventListener('click', function () {
                const cartKey = this.getAttribute('data-cart-key');
            showConfirm(
                translations['are_you_sure_you_want_to_remove_this_item'], 
                function() {
                    removeItemFromCart(cartKey);
                }
            );
            });
        }
    });





    // Check if the modal close button exists
    var closeModalButton = document.getElementById("closeModal");
    if (closeModalButton) {
        closeModalButton.addEventListener("click", function () {
            document.getElementById("pricePreviewModal").style.display = "none";
        });
    }

}


document.addEventListener('DOMContentLoaded', function () {
    const sliderWrapper = document.querySelector('.product-images-slider');
    if (!sliderWrapper) return; // Exit if no slider on this page

    const slides = sliderWrapper.querySelector('.slides');
    const prevSlideBtn = sliderWrapper.querySelector('.prev-slide');
    const nextSlideBtn = sliderWrapper.querySelector('.next-slide');
    const thumbnails = sliderWrapper.querySelectorAll('.thumbnail-image');
    const sliderContainer = sliderWrapper.querySelector('.slider-container');

    // Exit if essential elements are missing
    if (!slides || !prevSlideBtn || !nextSlideBtn || !sliderContainer) return;

    const isRTL = (typeof currentLanguage !== 'undefined' && currentLanguage === 'ar');
    const totalSlides = slides.children.length;
    let currentIndex = 0;

    // Hide controls if there's only one image
    if (totalSlides <= 1) {
        prevSlideBtn.style.display = 'none';
        nextSlideBtn.style.display = 'none';
        return; // No need for any slider logic
    }

    // --- Core Function to Move Slider and Update Thumbnails ---
    function goToSlide(index) {
        // Update the main index
        currentIndex = index;

        // Update the main slider's position
        const offset = isRTL ? currentIndex * 100 : -currentIndex * 100;
        slides.style.transform = `translateX(${offset}%)`;

        // Update the active state on thumbnails
        thumbnails.forEach((thumb, thumbIndex) => {
            if (thumbIndex === currentIndex) {
                thumb.classList.add('active');
            } else {
                thumb.classList.remove('active');
            }
        });
    }

    // --- Event Listeners ---

    // Next Button (with looping)
    nextSlideBtn.addEventListener('click', () => {
        const nextIndex = (currentIndex + 1) % totalSlides; // Loop back to 0 if at the end
        goToSlide(nextIndex);
    });

    // Previous Button (with looping)
    prevSlideBtn.addEventListener('click', () => {
        const prevIndex = (currentIndex - 1 + totalSlides) % totalSlides; // Loop to the end if at 0
        goToSlide(prevIndex);
    });

    // Thumbnail Clicks
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', () => {
            const newIndex = parseInt(thumb.dataset.index, 10);
            goToSlide(newIndex);
        });
    });

    // Touch Support (with looping)
    let startX;
    sliderContainer.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
    }, { passive: true });

    sliderContainer.addEventListener('touchmove', (e) => {
        if (!startX) return;
        const moveX = e.touches[0].clientX;
        const diff = startX - moveX;

        // Check for a significant swipe to avoid accidental triggers
        if (Math.abs(diff) > 50) {
            if (diff > 0) { // Swipe left
                nextSlideBtn.click(); // Trigger the next button's logic
            } else { // Swipe right
                prevSlideBtn.click(); // Trigger the previous button's logic
            }
            startX = null; // Reset startX to prevent multiple swipes in one gesture
        }
    }, { passive: true });

    // Initialize the slider to the first slide
    goToSlide(0);
});



// document.addEventListener('DOMContentLoaded', function () {
//     const sliderContainer = document.querySelector('.slider-container');
//     const slides = document.querySelector('.slides');
//     const prevSlide = document.querySelector('.prev-slide');
//     const nextSlide = document.querySelector('.next-slide');

//     if (sliderContainer && slides && prevSlide && nextSlide) {  // Check if elements exist
//         const isRTL = (currentLanguage === 'ar'); // Check if the language is Arabic
//         let currentIndex = 0;  // Track the current slide
//         const totalSlides = document.querySelectorAll('.slides img').length; // Count the total images

//         // Function to update the slide position based on LTR or RTL
//         function updateSlidePosition() {
//             if (isRTL) {
//                 // In RTL, we reverse the direction by using a positive translateX
//                 slides.style.transform = `translateX(${currentIndex * 100}%)`;
//             } else {
//                 // In LTR, we move normally to the left
//                 slides.style.transform = `translateX(-${currentIndex * 100}%)`;
//             }
//         }

//         // Handle next slide
//         nextSlide.addEventListener('click', () => {
//             if (currentIndex < totalSlides - 1) {
//                 currentIndex++;
//                 updateSlidePosition();
//             }
//         });

//         // Handle previous slide
//         prevSlide.addEventListener('click', () => {
//             if (currentIndex > 0) {
//                 currentIndex--;
//                 updateSlidePosition();
//             }
//         });

//         // Optional: Add touch support for mobile
//         let startX;
//         sliderContainer.addEventListener('touchstart', (e) => {
//             startX = e.touches[0].clientX;
//         });
//         sliderContainer.addEventListener('touchmove', (e) => {
//             if (!startX) return;
//             const moveX = e.touches[0].clientX;
//             const diff = startX - moveX;

//             // Swipe left for next slide
//             if (diff > 50) {
//                 if (currentIndex < totalSlides - 1) {
//                     currentIndex++;
//                     updateSlidePosition();
//                 }
//             }
//             // Swipe right for previous slide
//             if (diff < -50) {
//                 if (currentIndex > 0) {
//                     currentIndex--;
//                     updateSlidePosition();
//                 }
//             }
//             startX = null;
//         });
//     }
// });


function handleUpdateCartQuantity() {
    const addToCartButton = document.getElementById('add-to-cart-button');
    const quantityInput = document.getElementById('quantity-input');
    const productId = parseInt(addToCartButton.dataset.productId);
    const productSizeId = parseInt(addToCartButton.dataset.productSizeId);
    const quantity = parseInt(quantityInput.value);
    const was_not_item_in_cart = addToCartButton.textContent.trim() === translations['Add_to_Cart'];

    if (!productSizeId) {
        showToast(translations['please_select_a_size_first'], 'error');
        return;
    }

    if (isNaN(quantity) || quantity < 0) {
        showToast(translations['invalid_quantity_format'], 'error');
        return;
    }

    const availableQuantity = parseInt(quantityInput.max);
    if (quantity > availableQuantity) {
        showToast(translations['cannot_add_more_than_available'], 'error');
        return;
    }

    fetch('/update_cart_quantity', {
        method: 'POST',
        body: JSON.stringify({
            product_id: productId,
            product_size_id: productSizeId,
            quantity: quantity
        }),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {

            if (data.new_quantity > 0 && was_not_item_in_cart) {
                showToast(translations['item_added_to_cart_successfully'], 'succeed');
            } else {
                showToast(translations['cart_updated_successfully'], 'succeed');
            }


            if (data.new_quantity > 0) {
                addToCartButton.innerHTML = `${translations['Update_Cart']} &#x2000;<i class="fas fa-shopping-cart"></i>`;
            } else {
                addToCartButton.innerHTML = `${translations['Add_to_Cart']} &#x2000;<i class="fas fa-shopping-cart"></i>`;
            }

            updateCartCount(data.cart_count);
            quantityInput.value = data.new_quantity > 0 ? data.new_quantity : 0;
        } else {
            showToast(data.message || translations['Error_while_updating_cart'], 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast(translations['Error_while_updating_cart'], 'error');
    });
}

function ordercardPlusButton(cartKey) {
    // Get the current quantity displayed in the cart
    var currentQuantityElement = document.querySelector(`.summary-card p button.ordercard-plus-button[data-cart-key="${cartKey}"]`).nextElementSibling;
    var currentQuantityInCart = parseInt(currentQuantityElement.textContent.split(' ')[0]); // Assuming format "X x Y"

    // Get the available quantity from the data attribute of the button
    var availableQuantity = parseInt(document.querySelector(`.summary-card p button.ordercard-plus-button[data-cart-key="${cartKey}"]`).dataset.availableQuantity);

    // Client-side check
    if (currentQuantityInCart + 1 > availableQuantity) {
        // alert(translations["cannot_add_more_than_available"]);
        showToast(translations['cannot_add_more_than_available'], 'error');
        return; // Prevent the fetch request
    }

    fetch('/ordercard_plus_button', {
        method: 'POST',
        body: JSON.stringify({ cart_key: cartKey }),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const qty = data.new_quantity ?? data.order?.[cartKey]?.quantity;
            console.log("Increased:", cartKey, "Quantity:", qty);
            updateCartCount(data.cart_count);
            updateOrderSummary();
        } else {
            console.error("Error increasing product:", data.message);
            if (data.code === "not_enough_stock") {
                // alert(translations["cannot_add_more_than_available"]);
                showToast(translations['cannot_add_more_than_available'], 'error');
            } else {
                // alert(data.message);
                showToast(data.message, 'error');
            }
        }
    }).catch(error => {
        console.error('Error:', error);
        // alert(translations['Error_while_increasing_quantity']);
        showToast(translations['Error_while_increasing_quantity'], 'error');
    });
}


function ordercardMinusButton(cartKey) { // Changed to cartKey
    fetch('/ordercard_minus_button', {
        method: 'POST',
        body: JSON.stringify({ cart_key: cartKey }), // Pass cart_key
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const qty = data.new_quantity ?? data.order?.[cartKey]?.quantity ?? 0;
                console.log("Removed:", cartKey, "Quantity:", qty);

                updateCartCount(data.cart_count);
                updateOrderSummary();
            } else {
                console.error("Error removing product.");
                // alert(data.message); // Display error message from server
                showToast(data.message, 'error');
            }
        }).catch(error => {
            console.error('Error:', error);
            // alert(translations['Error_while_decreasing_quantity']); // Generic error
            showToast(translations['Error_while_decreasing_quantity'], 'error');
        });
}


function removeItemFromCart(cartKey) {
    fetch('/remove_from_cart', {
        method: 'POST',
        body: JSON.stringify({ cart_key: cartKey }),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("Removed item:", cartKey);
            updateCartCount(data.cart_count);
            // The most reliable way to update the view is to call updateOrderSummary
            updateOrderSummary(); 
        } else {
            showToast(data.message || 'Error removing item', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error removing item from cart.', 'error');
    });
}

function updateCartCount(newCount) {
    const cartButton = document.querySelector('.cart-count');
    if (cartButton) {
        cartButton.innerHTML = `${newCount}`;
    }
}



function updateOrderSummary() {
    fetch('/get_order_summary', {
        headers: {
            'X-CSRFToken': csrfToken // Ensure CSRF token is sent with GET requests if needed, though usually not for GET
        }
    })
        .then(response => response.json())
        .then(data => {
            let summaryBox = document.querySelector('.summary-box-card');
            let orderHtml = `<h2>${translations['Current_Order']}</h2><br>`; // Use a temporary variable to build HTML

            if (data.order_items.length > 0) {
                data.order_items.forEach(item => {
                    const itemCartKey = `${item.product_id}_${item.product_size_id}`;
                    orderHtml += `
                        <div class="summary-card" style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
                            <a href="/product/${item.product_id}?product_size_id=${item.product_size_id}" class="product-link">
                            <img src="${item.image_url.startsWith('http') ? item.image_url : '/static/' + item.image_url}" alt="${currentLanguage === 'ar' ? item.name_ar : item.name_en} - Product Thumbnail" style="border: 1px solid lightgray; height: 75px; width: auto; border-radius: 5px; object-fit: cover;">
                            </a>
                            <div style="flex-grow: 1;">
                                <a href="/product/${item.product_id}?product_size_id=${item.product_size_id}" class="product-link">
                                    ${(currentLanguage === 'ar' ? item.name_ar : item.name_en)}
                                </a>
                                <p>${(currentLanguage === 'ar' ? item.size_ar : item.size_en)}</p>
                                
                                <p style="margin: 5px 0 0 0;">
                                    <button class="ordercard-plus-button" data-cart-key="${item.product_id}_${item.product_size_id}" data-available-quantity="${item.available_quantity}">+</button>
                                    <span style="padding: 0 5px; font-weight: bold;">${item.quantity}</span>
                                    <button class="ordercard-minus-button" data-cart-key="${item.product_id}_${item.product_size_id}">−</button>
                                    <span style="color:gray;"> × ${item.price.toFixed(2)} ${translations['EGP']}</span>
                                </p>
                            </div>
                            <button class="remove-item-button" data-cart-key="${item.product_id}_${item.product_size_id}" style="background: none; border: none; font-size: 25px !important; font-weight: bold !important; color: red; cursor: pointer;" onmouseover="this.style.color='black';" onmouseout="this.style.color='red';">&times;</button>
                        </div>`;
                });

                orderHtml += `
                    <h2><b>${translations['Total_Price']}: ${data.total_price.toFixed(2)} ${translations['EGP']}</b></h2>`;
                
                if (data.delivery_fees > 0 && data.total_price > 0) {
                    orderHtml += `
                        <p><b>${translations['Delivery_Fees']}: ${data.delivery_fees.toFixed(2)} ${translations['EGP']}</b></p>
                        <h2><b>${translations['Grand_Total']}: ${data.grand_total.toFixed(2)} ${translations['EGP']}</b></h2>`;
                }

                let sendOrderSectionHtml = '';
                if (data.is_serviceable) {
                    // If serviceable, create just the button.
                    sendOrderSectionHtml = `
                        <input type="submit" value="${translations['Send_Order']}" style="background-color: rgb(255, 153, 0); font-size: 20px !important;" onsubmit="applyPromoCode();">
                    `;
                } else {
                    // If not serviceable, create the warning message AND the disabled button.
                    sendOrderSectionHtml = `
                        <div class="alert alert-warning" style="padding: 10px; margin-bottom: 10px; border: 1px solid #ffc107; border-radius: 5px; background-color: #fff3cd; color: #856404; text-align: center;">
                            ${translations['delivery_not_covered_for_this_area_yet']}
                        </div>
                        <input type="submit" value="${translations['Send_Order']}" disabled style="background-color: #ccc; cursor: not-allowed; font-size: 20px !important;">
                    `;
                }


                orderHtml += `
                    <input type="hidden" id="orderData" value="${data.order_items.length > 0}">
                    <h2><b><span id="orderDataMessage"></span></b></h2>
                    
                    <div class="order-container">
                        <form id="applyPromoCodeForm" onsubmit="event.preventDefault(); applyPromoCode();">
                            <div class="form-group" style="min-width: 190px !important; max-width: 190px !important; font-size: 20px !important;">
                                <input type="text" name="promocode" id="promocode" placeholder="${translations['Promo_Code']}" required>
                                <input type="submit" value="${translations['Apply_PromoCode']}" style="font-size: 15px !important;">
                            </div>
                        </form>
                        <br>
                        <form action="/send_order" method="post" onsubmit="return validateOrder();">
                            <input type="hidden" name="csrf_token" value="${csrfToken}">
                            <div class="form-group" style="min-width: 190px !important; max-width: 190px !important; font-size: 20px !important;">
                                ${translations['Payment_Method']}: 
                                <select id="payment-method" name="payment_method" style="font-size: 20px !important;" required>
                                    <option value="" disabled ${!data.last_payment_method ? "selected" : ""}></option>
                                    <option value="Bank Card" ${data.last_payment_method === "Bank Card" ? "selected" : ""}>${translations['Bank_Card']}</option>
                                    <option value="Cash on Delivery" ${data.last_payment_method === "Cash on Delivery" ? "selected" : ""}>${translations['Cash_on_Delivery']}</option>
                                </select>
                                <input type="text" name="promocode" id="promocode-hidden" placeholder="${translations['Promo_Code']}">    
                                ${sendOrderSectionHtml}
                            </div>
                        </form>
                        <br>
                        <form action="/clear_order" method="post" onsubmit="return validateOrder();">
                            <input type="hidden" name="csrf_token" value="${csrfToken}">
                            <div class="form-group" style="min-width: 190px !important; max-width: 190px !important; font-size: 20px !important;">
                                <input type="submit" value="${translations['Clear_Order']}" style="color: gray !important; background-color: lightgray !important; font-size: 20px !important;">
                            </div>
                        </form>                        
                    </div>`;

                summaryBox.innerHTML = orderHtml; // Assign built HTML to summaryBox
                reapplyEventListeners();

            } else {
                // This block handles the case where the cart is empty
                orderHtml += `<p>${translations['No_order']}</p>
                 <h2><b>${translations['Total_Price']}: ${data.total_price.toFixed(2)} ${translations['EGP']}</b></h2>`;
                
                if (data.delivery_fees > 0 && data.total_price > 0) { // Still check, though likely 0
                    orderHtml += `
                        <p><b>${translations['Delivery_Fees']}: ${data.delivery_fees.toFixed(2)} ${translations['EGP']}</b></p>
                        <h2><b>${translations['Grand_Total']}: ${data.grand_total.toFixed(2)} ${translations['EGP']}</b></h2>`;
                }

                let sendOrderSectionHtml = '';
                if (data.is_serviceable) {
                    // If serviceable, create just the button.
                    sendOrderSectionHtml = `
                        <input type="submit" value="${translations['Send_Order']}" style="background-color: rgb(255, 153, 0); font-size: 20px !important;" onsubmit="applyPromoCode();">
                    `;
                } else {
                    // If not serviceable, create the warning message AND the disabled button.
                    sendOrderSectionHtml = `
                        <div class="alert alert-warning" style="padding: 10px; margin-bottom: 10px; border: 1px solid #ffc107; border-radius: 5px; background-color: #fff3cd; color: #856404; text-align: center;">
                            ${translations['delivery_not_covered_for_this_area_yet']}
                        </div>
                        <input type="submit" value="${translations['Send_Order']}" disabled style="background-color: #ccc; cursor: not-allowed; font-size: 20px !important;">
                    `;
                }

                orderHtml += `
                 <input type="hidden" id="orderData" value="${data.order_items.length > 0}">
                 <h2><b><span id="orderDataMessage"></span></b></h2>
                 
                 <div class="order-container">
                     <form id="applyPromoCodeForm" onsubmit="event.preventDefault(); applyPromoCode();">
                         <div class="form-group" style="min-width: 190px !important; max-width: 190px !important; font-size: 20px !important;">
                             <input type="text" name="promocode" id="promocode" placeholder="${translations['Promo_Code']}" required>
                             <input type="submit" value="${translations['Apply_PromoCode']}" style="font-size: 15px !important;">
                         </div>
                     </form>
                     <br>
                     <form action="/send_order" method="post" onsubmit="return validateOrder();">
                        <input type="hidden" name="csrf_token" value="${csrfToken}">
                         <div class="form-group" style="min-width: 190px !important; max-width: 190px !important; font-size: 20px !important;">
                             ${translations['Payment_Method']}: 
                             <select id="payment-method" name="payment_method" style="font-size: 20px !important;" required>
                                 <option value="" disabled ${!data.last_payment_method ? "selected" : ""}></option>
                                 <option value="Bank Card" ${data.last_payment_method === "Bank Card" ? "selected" : ""}>${translations['Bank_Card']}</option>
                                 <option value="Cash on Delivery" ${data.last_payment_method === "Cash on Delivery" ? "selected" : ""}>${translations['Cash_on_Delivery']}</option>
                             </select>
                             <input type="text" name="promocode" id="promocode-hidden" placeholder="${translations['Promo_Code']}">
                             ${sendOrderSectionHtml}
                         </div>
                     </form>
                     <br>
                     <form action="/clear_order" method="post" onsubmit="return validateOrder();">
                        <input type="hidden" name="csrf_token" value="${csrfToken}">
                         <div class="form-group" style="min-width: 190px !important; max-width: 190px !important; font-size: 20px !important;">
                             <input type="submit" value="${translations['Clear_Order']}" style="color: gray !important; background-color: lightgray !important; font-size: 20px !important;">
                         </div>
                     </form>                     
                 </div>`;
                 summaryBox.innerHTML = orderHtml; // Assign built HTML to summaryBox
                 reapplyEventListeners();
            }
        }).catch(error => {
            console.error('Error updating order summary:', error);
        });
}



function applyPromoCode() {
    let promoCode = document.getElementById("promocode").value;

    fetch("/apply_promocode", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            'X-CSRFToken': csrfToken
        },
        body: `promocode=${encodeURIComponent(promoCode)}`
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                document.getElementById("pricePreviewContent").innerHTML = `
                <p><strong>${translations['Original_Total_Price']}: ${data.total_price.toFixed(2)} ${translations['EGP']}</strong></p>
                <p><strong>${translations['Discount_That_Will_Be_Applied']}: ${data.discount_percent}%</strong></p>
                <p><strong>${translations['new_total_price']}: ${data.new_total_price.toFixed(2)} ${translations['EGP']}</strong></p>
                <p><strong>${translations['new_grand_total']}: ${data.new_grand_total.toFixed(2)} ${translations['EGP']}</strong></p>
            `;
                document.getElementById("pricePreviewModal").style.display = "block";  // Show modal
                document.getElementById("promocode-hidden").value = promoCode;
            } else {
                // alert(data.message);  // Show an error message
                showToast(data.message, 'error');
            }
        })
        .catch(error => {
            console.error(error);
            // alert(translations['error_while_applying_promocode']);
            showToast(translations['error_while_applying_promocode'], 'error');
        });
}



// Function to add a new product row in admin_edit_order.html
function addProductRow() {
    var container = document.getElementById('new-products-container');
    var newRow = document.createElement('div');
    newRow.className = 'product-add-row'; // Add a class for easier removal
    newRow.innerHTML = `
        <div class="edit-order-group">
            ${translations['Product_Name']}
            <select name="new_product_id[]" onchange="loadProductSizes(this.value, this.parentNode.nextElementSibling.querySelector('select'))" required>
                <option value="">${translations['Select_a_product']}</option>
                ${product_names.map(product => `<option value="${product[0]}">${product[1]}</option>`).join('')}
            </select>
        </div>
        <div class="edit-order-group">
            ${translations['Product_Size']}
            <select name="new_product_size_id[]" required>
                <option value="">${translations['Select_a_size']}</option>
            </select>
        </div>
        <div class="edit-order-group">
            ${translations['Quantity']}
            <input type="number" name="new_product_quantity[]" min="1" value="1" required>
        </div>
        <div class="edit-order-group">
            <button type="button" onclick="removeProductRow(this)">${translations['remove_row']}</button>
        </div>        
    `;
    container.appendChild(newRow);
    rowCounter++;
}

// Function to remove a product row in admin_edit_order.html
function removeProductRow(button) {
    button.closest('.product-add-row').remove(); // Use closest to find the parent row
}

// Function to load product sizes via AJAX
function loadProductSizes(productId, sizeSelectElement) {
    if (!productId) {
        sizeSelectElement.innerHTML = '<option value="">' + translations['Select_a_size'] + '</option>';
        return;
    }
    fetch(`/api/product/${productId}/sizes`)
        .then(response => response.json())
        .then(data => {
            sizeSelectElement.innerHTML = '<option value="">' + translations['Select_a_size'] + '</option>';
            if (data.success && data.sizes.length > 0) {
                data.sizes.forEach(size => {
                    const option = document.createElement('option');
                    option.value = size.id;
                    option.textContent = currentLanguage === 'ar' ? size.size_ar + ' - ' + size.price + ' ' + translations['EGP'] + ' - ' + size.available_quantity : size.size_en + ' - ' + size.price + ' ' + translations['EGP'] + ' - ' + size.available_quantity;
                    sizeSelectElement.appendChild(option);
                });
            } else {
                console.warn('No sizes found for product ID:', productId);
            }
        })
        .catch(error => {
            console.error('Error loading product sizes:', error);
            sizeSelectElement.innerHTML = '<option value="">' + translations['Error_loading_sizes'] + '</option>';
        });
}

// Function to submit new products in admin_edit_order.html
function submitNewProducts(orderId) {
    var form = document.getElementById('new-products-form');
    var formData = new FormData(form);
    
    // Client-side validation for selected products and quantities
    let isValid = true;
    const productSelects = form.querySelectorAll('select[name="new_product_id[]"]');
    const sizeSelects = form.querySelectorAll('select[name="new_product_size_id[]"]');
    const quantityInputs = form.querySelectorAll('input[name="new_product_quantity[]"]');

    if (productSelects.length === 0) {
        // alert(translations['Please_add_at_least_one_product']);
        showToast(translations['Please_add_at_least_one_product'], 'error');
        return;
    }

    for (let i = 0; i < productSelects.length; i++) {
        if (!productSelects[i].value) {
            // alert(translations['Please_select_a_product_for_all_rows']);
            showToast(translations['Please_select_a_product_for_all_rows'], 'error');
            isValid = false;
            break;
        }
        if (!sizeSelects[i].value) {
            // alert(translations['Please_select_a_size_for_all_products']);
            showToast(translations['Please_select_a_size_for_all_products'], 'error');
            isValid = false;
            break;
        }
        const quantity = parseInt(quantityInputs[i].value);
        if (isNaN(quantity) || quantity < 1) { // Added isNaN check
            // alert(translations['Quantity_must_be_at_least_1']);
            showToast(translations['Quantity_must_be_at_least_1'], 'error');
            isValid = false;
            break;
        }
    }

    if (!isValid) {
        return;
    }

    fetch(`/admin/orders/admin_add_product_to_order/${orderId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    }).then(response => {
        if (response.ok) {
            location.reload();  // Reload page on success
        } else {
            // Handle error response (now expects JSON)
            return response.json().then(errorData => {
                // alert(errorData.message); // Display the error message from the server
                showToast(errorData.message, 'error');
            }).catch(() => {
                // Fallback if response is not valid JSON
                // alert(translations['Error_while_adding_products']);
                showToast(translations['Error_while_adding_products'], 'error');
            });
        }
    }).catch(error => {
        console.error('Error adding new products:', error);
        // alert(translations['Error_while_adding_products']);
        showToast(translations['Error_while_adding_products'], 'error');
    });
}


function updateStatusOptions(selectElement) {
    const currentStatus = selectElement.dataset.currentStatus;
    const options = {
        'Pending': ['Pending', 'Preparing', 'Delivering', 'Delivered', 'Cancelled'],
        'Preparing': ['Preparing', 'Pending', 'Delivering', 'Delivered', 'Cancelled'],
        'Delivering': ['Delivering', 'Delivered'],
        'Delivered': ['Delivered'],
        'Cancelled': ['Cancelled']
    };
    const allowedOptions = options[currentStatus];
    selectElement.innerHTML = '';
    allowedOptions.forEach(status => {
        const option = document.createElement('option');
        option.value = status;
        option.textContent = status;
        const translatedStatus = translations[status] || status; // Fallback to the original status if translation is missing
        option.textContent = translatedStatus;        
        if (status === currentStatus) {
            option.selected = true;
        }
        selectElement.appendChild(option);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const statusSelectElements = document.querySelectorAll('select[data-current-status]');
    statusSelectElements.forEach(select => {
        updateStatusOptions(select);
    });
});


// Fade out success messages automatically after 10 seconds
setTimeout(function () {
    const flashMessages = document.querySelectorAll('.flashes li.success');
    flashMessages.forEach(function (msg) {
        msg.classList.add('fade-out');
        setTimeout(() => {
            msg.style.display = 'none';
        }, 500);
    });
}, 10000);

// Close button handler (works for both danger & success)
document.addEventListener('DOMContentLoaded', function () {
    const closeButtons = document.querySelectorAll('.flash-close');
    closeButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const parent = this.parentElement;
            parent.classList.add('fade-out');
            setTimeout(() => {
                parent.style.display = 'none';
            }, 500);
        });
    });
});




// function validatePassword() {
//     var password = document.getElementById("password").value;
//     var message = document.getElementById("passwordMessage");
//     // Validate password length and spaces
//     if (password.length < 6 || /\s/.test(password)) {
//         message.style.color = 'red';
//         message.textContent = translations['Password_must_be_6_characters_and_no_spaces'];
//         return false;
//     } else {
//         message.textContent = '';
//         return true;
//     }
// }

// function validatePassword() {
//     var password = document.getElementById("password").value;
//     var message = document.getElementById("passwordMessage");
    
//     // Pattern: At least 8 chars, no spaces, at least one lowercase, one uppercase, one digit, one special char
//     var pattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s])[^\s]{8,}$/;

//     if (!pattern.test(password)) {
//         message.style.color = 'red';
//         message.textContent = translations['Password_complexity_error'];
//         return false;
//     } else {
//         message.textContent = '';
//         return true;
//     }
// }

function validatePassword() {
    const password = document.getElementById("password").value;
    const message = document.getElementById("passwordMessage");

    // Rule 1: Check length (at least 8 characters)
    if (password.length < 8) {
        message.style.color = 'red';
        message.textContent = translations['Password_length_error'];
        return false;
    }

    // Rule 2: Check for spaces
    if (/\s/.test(password)) {
        message.style.color = 'red';
        message.textContent = translations['Password_spaces_error'];
        return false;
    }

    // Rule 3: Check for at least one uppercase letter
    if (!/[A-Z]/.test(password)) {
        message.style.color = 'red';
        message.textContent = translations['Password_uppercase_error'];
        return false;
    }

    // Rule 4: Check for at least one lowercase letter
    if (!/[a-z]/.test(password)) {
        message.style.color = 'red';
        message.textContent = translations['Password_lowercase_error'];
        return false;
    }

    // Rule 5: Check for at least one number
    if (!/[0-9]/.test(password)) {
        message.style.color = 'red';
        message.textContent = translations['Password_number_error'];
        return false;
    }

    // // Rule 6: Check for at least one special character
    // if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    //     message.style.color = 'red';
    //     message.textContent = translations['Password_special_char_error'];
    //     return false;
    // }

    // If all checks pass, clear the message
    message.textContent = '';
    return true;
}


function confirmPassword() {
    var password = document.getElementById("password").value;
    var confirmPassword = document.getElementById("confirm_password").value;
    var message = document.getElementById("passwordMessage");
    // Validate password confirmation
    if (password !== confirmPassword) {
        message.style.color = 'red';
        message.textContent = translations['Passwords_do_not_match'];
        return false;
    } else {
        message.textContent = '';
        return true;
    }
}

function validateUsername() {
    // Get the username input element
    var username = document.getElementById("username").value;
    var message = document.getElementById("usernameMessage");
    var emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailRegex.test(username)) {
        message.style.color = 'red';
        message.textContent = translations['Invalid_email_address_format'];
        return false;
    } else {
        message.textContent = '';
        return true;
    }
}

function validateAndConfirmPassword() {
    // Validate both password criteria and confirmation
    return validatePassword() && confirmPassword() && validateUsername();
}

function validateLoginForm() {
    var username = document.getElementById("username").value.trim();
    var password = document.getElementById("password").value.trim();
    var messageContainer = document.getElementById('loginMessage');
    // Clear any previous messages
    messageContainer.textContent = '';
    // Basic client-side validation
    if (username === "" || password === "") {
        messageContainer.style.color = 'red';
        messageContainer.textContent = translations['Please_enter_both_username_and_password'];
        return false;  // Prevent form submission
    }
    // Allow form submission; server will handle authentication
    return true;
}

function validateOrder() {
    // Get the value of the hidden input to check if there are items in the order
    var orderData = document.getElementById("orderData").value;
    var messageContainer = document.getElementById('orderDataMessage');
    messageContainer.textContent = '';

    // Check if the order is empty
    if (orderData === 'false') {
        messageContainer.style.color = 'red';
        messageContainer.textContent = translations['No_Items_In_Order'];
        return false; // Prevent form submission
    }

    return true;
}


function validateDeleteAdmin(form) {
    // Get the value of the hidden input to check if the client is a superadmin
    var isSuperAdmin = form.querySelector('input[type="submit"]').getAttribute('data-superadmin');
    var messageContainer = document.getElementById('isSuperAdminMessage');
    messageContainer.textContent = '';
    // Check if the order is empty
    if (isSuperAdmin === 'true') {
        messageContainer.style.color = 'red';
        messageContainer.textContent = translations['Cannot_Delete_Super_Admin_Account'];
        return false; // Prevent form submission
    }
    return true;
}


function validateOrderEdit(orderId) {
    // Get the values of the hidden inputs for the specific order
    var orderStatus = document.getElementById("orderStatus_" + orderId).value;
    var messageContainer = document.getElementById('orderEditMessage_' + orderId);

    // Clear any previous messages
    messageContainer.textContent = '';

    // Check if the order status allows editing
    if (orderStatus !== "Pending" && orderStatus !== "Preparing") {
        messageContainer.style.color = 'red';
        messageContainer.textContent = translations['Edit_order_status_Pending_Preparing'];
        return false; // Prevent navigation
    }

    // If all conditions are met, allow navigation
    return true;
}


function validateOrderCancel(orderId) {
    // Get the values of the hidden inputs for the specific order
    var orderStatus = document.getElementById("orderCancel_" + orderId).value;
    var messageContainer = document.getElementById('orderCancelMessage_' + orderId);

    // Clear any previous messages
    messageContainer.textContent = '';

    // Check if the order status allows editing
    if (orderStatus !== "Pending" && orderStatus !== "Preparing") {
        messageContainer.style.color = 'red';
        messageContainer.textContent = translations['you_can_only_cancel_orders_with_status_pending_or_preparing'];
        return false; // Prevent navigation
    }

    // If all conditions are met, allow navigation
    return true;
}




/**
 * Shows a custom toast notification.
 * @param {string} message The message to display.
 * @param {string} type The type of toast ('success' or 'error'), for styling. Defaults to normal.
 * @param {number} duration How long to show the toast in milliseconds. Defaults to 3000 (3 seconds).
 */
function showToast(message, type = '', duration = 3000) {
    // Find the toast element in the DOM
    const toast = document.getElementById("custom-toast");
    if (!toast) return; // Do nothing if the toast element doesn't exist

    // Set the message content
    toast.textContent = message;

    // Reset classes and add the new ones
    toast.className = "custom-toast"; // Reset to base class
    if (type) {
        toast.classList.add(type); // Add 'success' or 'error' class if provided
    }
    toast.classList.add("show"); // Add 'show' class to trigger the fade-in animation

    // After 'duration' milliseconds, remove the 'show' class to trigger the fade-out
    setTimeout(function() {
        toast.classList.remove("show");
    }, duration);
}




/**
 * Shows a custom confirmation modal.
 * @param {string} message The question to ask the user.
 * @param {function} onConfirm The function to execute if the user clicks "Yes".
 */
function showConfirm(message, onConfirm) {
    const modal = document.getElementById('custom-confirm-modal');
    const modalText = document.getElementById('confirm-modal-text');
    const yesBtn = document.getElementById('confirm-modal-yes-btn');
    const noBtn = document.getElementById('confirm-modal-no-btn');

    if (!modal || !modalText || !yesBtn || !noBtn) return;

    // Set the message
    modalText.textContent = message;

    // Show the modal
    modal.style.display = 'flex';

    // Create new "clean" buttons to avoid duplicate event listeners
    const newYesBtn = yesBtn.cloneNode(true);
    const newNoBtn = noBtn.cloneNode(true);
    yesBtn.parentNode.replaceChild(newYesBtn, yesBtn);
    noBtn.parentNode.replaceChild(newNoBtn, noBtn);

    // If "Yes" is clicked, hide the modal and run the onConfirm function
    newYesBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        onConfirm(); // Execute the callback function
    });

    // If "No" is clicked, just hide the modal
    newNoBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
}




/**
 * Shows a custom confirmation modal.
 * @param {string} message The question to ask the user.
 * @param {HTMLElement} elementToSubmit The HTML form element to submit if the user confirms.
 */
function showConfirmAndSubmit(message, elementToSubmit) {
    const modal = document.getElementById('custom-confirm-modal');
    const modalText = document.getElementById('confirm-modal-text');
    const yesBtn = document.getElementById('confirm-modal-yes-btn');
    const noBtn = document.getElementById('confirm-modal-no-btn');

    if (!modal || !modalText || !yesBtn || !noBtn) {
        // Fallback to the basic browser confirm if the modal elements aren't found
        if (confirm(message)) {
            elementToSubmit.submit();
        }
        return;
    }

    // Set the message
    modalText.textContent = message;

    // Show the modal
    modal.style.display = 'flex';

    // Create new "clean" buttons to avoid duplicate event listeners
    const newYesBtn = yesBtn.cloneNode(true);
    const newNoBtn = noBtn.cloneNode(true);
    yesBtn.parentNode.replaceChild(newYesBtn, yesBtn);
    noBtn.parentNode.replaceChild(newNoBtn, noBtn);

    // --- Event Handlers ---

    // If "Yes" is clicked, hide the modal and submit the provided element
    newYesBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        if (elementToSubmit && typeof elementToSubmit.submit === 'function') {
            elementToSubmit.submit(); // Submit the form
        }
    });

    // If "No" is clicked, just hide the modal
    newNoBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

}

