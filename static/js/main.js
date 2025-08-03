// Main JavaScript functionality for Telegram Feed Aggregator - Work-ing

// Clean and format text for display (like Telegram)
function cleanTelegramText(text) {
    if (!text) return '';
    
    // Create a temporary div to decode HTML entities
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = text;
    let decoded = tempDiv.textContent || tempDiv.innerText || '';
    
    // Now clean the decoded text
    let cleaned = decoded
        // Convert literal \n to actual newlines
        .replace(/\\n/g, '\n')
        // Remove excessive whitespace but preserve single spaces and line breaks
        .replace(/[ \t]+/g, ' ')
        // Remove special unicode characters that are not emojis
        .replace(/[\u200B-\u200D\uFEFF]/g, '')
        // Replace multiple line breaks with double line breaks
        .replace(/\n{3,}/g, '\n\n')
        // Remove trailing/leading whitespace from each line
        .split('\n').map(line => line.trim()).join('\n')
        // Remove leading/trailing whitespace from entire text
        .trim();
    
    return cleaned;
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // Quick test to confirm JS is working
    console.log('JavaScript is working! Bootstrap check...');
    
    // Wait for Bootstrap to be available
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap is not loaded!');
        alert('⚠️ Bootstrap не загружен! Модальные окна не будут работать.');
        return;
    }
    
    console.log('✅ Bootstrap is available');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(function() {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 150);
            }
        }, 5000);
    });

    // Initialize post card clicks
    initializePostCardClicks();
    
    // Also try to initialize after a small delay to handle dynamic content
    setTimeout(function() {
        console.log('Secondary initialization after delay...');
        initializePostCardClicks();
    }, 1000);
});

// Initialize post card click handlers
function initializePostCardClicks() {
    const postCards = document.querySelectorAll('.post-card');
    console.log('Found post cards:', postCards.length);
    
    if (postCards.length === 0) {
        console.warn('No post cards found! Check if posts are loaded.');
        return;
    }
    
    postCards.forEach((card, index) => {
        console.log(`Checking card ${index + 1}:`, card);
        
        // Check if already initialized
        if (card.hasAttribute('data-click-initialized')) {
            console.log(`Card ${index + 1} already initialized, skipping`);
            return;
        };
        
        // Mark as initialized
        card.setAttribute('data-click-initialized', 'true');
        
        // Add event listener
        card.addEventListener('click', function(e) {
            console.log('Card clicked:', e.target);
            
            // Don't open modal if clicking on links or buttons
            if (e.target.closest('a, button, .contact-button')) {
                console.log('Click ignored - target is link or button');
                return;
            }
            
            console.log('Opening post modal for card:', card);
            openPostModal(card);
        });
        
        // Add cursor pointer style
        card.style.cursor = 'pointer';
        console.log(`Card ${index + 1} initialized with click handler`);
    });
    
    console.log('All post cards checked and initialized');
};

// Open post in modal
function openPostModal(postCard) {
    console.log('openPostModal called with:', postCard);
    
    try {
        // Get pre-rendered modal content from hidden div
        const modalContentDiv = postCard.querySelector('.modal-content-data');
        const modalContent = modalContentDiv ? modalContentDiv.innerHTML : '';
        
        console.log('Modal content available:', modalContent ? 'Yes' : 'No');
        console.log('Content length:', modalContent ? modalContent.length : 0);
        
        // Get modal elements
        const modalElement = document.getElementById('postModal');
        const modalContentElement = modalElement.querySelector('.modal-content');
        
        if (!modalElement || !modalContentElement) {
            console.error('Modal elements not found!');
            return;
        }
        
        // Use pre-rendered content from Jinja2
        if (modalContent && modalContent.trim() !== '') {
            modalContentElement.innerHTML = modalContent;
            console.log('Modal content set from Jinja2 template');
        } else {
            // Fallback content if modal content is missing
            console.warn('No modal content found, using fallback');
            modalContentElement.innerHTML = `
                <div class="modal-header">
                    <h5 class="modal-title">Пост</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Ошибка загрузки содержимого поста.</p>
                </div>
            `;
        }
        
        console.log('About to show modal using Bootstrap');
        
        // Show modal using Bootstrap
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
        console.log('Modal shown successfully');
        
    } catch (error) {
        console.error('Error in openPostModal:', error);
        alert('Ошибка при открытии модального окна: ' + error.message);
    }
}
