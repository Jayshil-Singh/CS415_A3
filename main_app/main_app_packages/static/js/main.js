// Notification System
class NotificationSystem {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;

        this.container.appendChild(notification);

        // Add close button functionality
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => this.remove(notification));

        // Auto remove after duration
        setTimeout(() => this.remove(notification), duration);

        // Add entrance animation
        setTimeout(() => notification.classList.add('show'), 10);
    }

    remove(notification) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }

    getIcon(type) {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        return icons[type] || icons.info;
    }
}

// Search System
class SearchSystem {
    constructor() {
        this.searchInput = document.querySelector('.search-input');
        if (this.searchInput) {
            this.setupSearch();
        }
    }

    setupSearch() {
        this.searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
    }

    async handleSearch(event) {
        const query = event.target.value.trim();
        if (query.length < 2) return;

        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const results = await response.json();
            this.displayResults(results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    displayResults(results) {
        const resultsContainer = document.querySelector('.search-results');
        if (!resultsContainer) return;

        resultsContainer.innerHTML = results.map(result => `
            <div class="search-result-item">
                <h4>${result.title}</h4>
                <p>${result.description}</p>
            </div>
        `).join('');
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Interactive Cards
class InteractiveCards {
    constructor() {
        this.cards = document.querySelectorAll('.interactive-card');
        this.setupCards();
    }

    setupCards() {
        this.cards.forEach(card => {
            card.addEventListener('mouseenter', () => this.handleCardHover(card));
            card.addEventListener('mouseleave', () => this.handleCardLeave(card));
            card.addEventListener('click', () => this.handleCardClick(card));
        });
    }

    handleCardHover(card) {
        card.classList.add('card-hover');
        const icon = card.querySelector('i');
        if (icon) {
            icon.classList.add('fa-bounce');
        }
    }

    handleCardLeave(card) {
        card.classList.remove('card-hover');
        const icon = card.querySelector('i');
        if (icon) {
            icon.classList.remove('fa-bounce');
        }
    }

    handleCardClick(card) {
        const link = card.getAttribute('data-href');
        if (link) {
            window.location.href = link;
        }
    }
}

// Initialize all interactive features when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize notification system
    window.notifications = new NotificationSystem();

    // Initialize search system
    window.search = new SearchSystem();

    // Initialize interactive cards
    window.cards = new InteractiveCards();

    // Add loading animation to action buttons
    document.querySelectorAll('.action-button').forEach(button => {
        button.addEventListener('click', (e) => {
            if (!button.getAttribute('data-href')) {
                e.preventDefault();
                notifications.show('This feature is coming soon!', 'info');
            }
        });
    });

    // Add smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}); 