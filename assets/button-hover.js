// Track mouse position on buttons for radial hover effect
document.addEventListener('DOMContentLoaded', function() {
    // Use event delegation to handle dynamically created buttons
    document.addEventListener('mousemove', function(e) {
        const button = e.target.closest('.btn-primary');
        if (button) {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            button.style.setProperty('--mouse-x', x + 'px');
            button.style.setProperty('--mouse-y', y + 'px');
        }
    });
});

