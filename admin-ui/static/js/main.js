/**
 * Main JavaScript for Policy Aggregator Admin UI
 */

// Dashboard interactivity
document.addEventListener('DOMContentLoaded', function() {
    // Handle click on recent changes rows
    const changeRows = document.querySelectorAll('table tbody tr');
    changeRows.forEach(row => {
        const link = row.querySelector('a[href^="/changes/"]');
        if (link) {
            // Make entire row clickable
            row.style.cursor = 'pointer';
            row.addEventListener('click', function(e) {
                // Don't navigate if clicking directly on the link
                if (e.target.tagName !== 'A') {
                    window.location.href = link.href;
                }
            });
        }
    });
    
    // Add hover effects for clickable rows
    changeRows.forEach(row => {
        if (row.style.cursor === 'pointer') {
            row.addEventListener('mouseenter', function() {
                this.classList.add('bg-indigo-50');
            });
            row.addEventListener('mouseleave', function() {
                this.classList.remove('bg-indigo-50');
            });
        }
    });
});

