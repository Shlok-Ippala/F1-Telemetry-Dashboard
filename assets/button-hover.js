// Track mouse position on buttons and cards for radial hover effect
document.addEventListener('DOMContentLoaded', function() {
    // Use event delegation to handle dynamically created elements
    document.addEventListener('mousemove', function(e) {
        // Check for btn-primary, home-btn, and feature-card classes
        const element = e.target.closest('.btn-primary, .home-btn, .feature-card');
        if (element) {
            const rect = element.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            element.style.setProperty('--mouse-x', x + 'px');
            element.style.setProperty('--mouse-y', y + 'px');
        }
    });
});

