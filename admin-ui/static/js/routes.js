/**
 * Routes list page functionality (search, filter, sort)
 */

let currentSort = {
    column: null,
    direction: 'asc'
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize search/filter
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', handleFilter);
    }
    
    // Initialize filter dropdowns
    const filterOrigin = document.getElementById('filterOrigin');
    const filterDestination = document.getElementById('filterDestination');
    const filterVisaType = document.getElementById('filterVisaType');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    if (filterOrigin) {
        populateFilterDropdowns();
        filterOrigin.addEventListener('change', handleFilter);
    }
    if (filterDestination) {
        filterDestination.addEventListener('change', handleFilter);
    }
    if (filterVisaType) {
        filterVisaType.addEventListener('change', handleFilter);
    }
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    // Initialize sorting
    const sortableHeaders = document.querySelectorAll('[data-sort]');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.getAttribute('data-sort');
            handleSort(column);
        });
    });
});

/**
 * Populate filter dropdowns with unique values from routes
 */
function populateFilterDropdowns() {
    const rows = document.querySelectorAll('.route-row');
    const originSet = new Set();
    const destinationSet = new Set();
    
    rows.forEach(row => {
        const origin = row.getAttribute('data-origin');
        const destination = row.getAttribute('data-destination');
        if (origin) originSet.add(origin);
        if (destination) destinationSet.add(destination);
    });
    
    // Populate origin dropdown
    const filterOrigin = document.getElementById('filterOrigin');
    if (filterOrigin) {
        const sortedOrigins = Array.from(originSet).sort();
        sortedOrigins.forEach(origin => {
            const option = document.createElement('option');
            option.value = origin;
            option.textContent = origin;
            filterOrigin.appendChild(option);
        });
    }
    
    // Populate destination dropdown
    const filterDestination = document.getElementById('filterDestination');
    if (filterDestination) {
        const sortedDestinations = Array.from(destinationSet).sort();
        sortedDestinations.forEach(destination => {
            const option = document.createElement('option');
            option.value = destination;
            option.textContent = destination;
            filterDestination.appendChild(option);
        });
    }
}

/**
 * Handle search/filter input and dropdowns
 */
function handleFilter() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase().trim() || '';
    const filterOrigin = document.getElementById('filterOrigin')?.value || '';
    const filterDestination = document.getElementById('filterDestination')?.value || '';
    const filterVisaType = document.getElementById('filterVisaType')?.value || '';
    
    const rows = document.querySelectorAll('.route-row');
    
    rows.forEach(row => {
        const origin = row.getAttribute('data-origin') || '';
        const destination = row.getAttribute('data-destination') || '';
        const visa = row.getAttribute('data-visa') || '';
        const email = row.getAttribute('data-email')?.toLowerCase() || '';
        
        // Check search term match
        const searchMatches = !searchTerm || 
            origin.toLowerCase().includes(searchTerm) ||
            destination.toLowerCase().includes(searchTerm) ||
            visa.toLowerCase().includes(searchTerm) ||
            email.includes(searchTerm);
        
        // Check filter matches
        const originMatches = !filterOrigin || origin === filterOrigin;
        const destinationMatches = !filterDestination || destination === filterDestination;
        const visaMatches = !filterVisaType || visa === filterVisaType;
        
        // Show row if all conditions match
        const matches = searchMatches && originMatches && destinationMatches && visaMatches;
        row.style.display = matches ? '' : 'none';
    });
    
    // Update "No routes found" message
    updateNoRoutesMessage();
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    const searchInput = document.getElementById('searchInput');
    const filterOrigin = document.getElementById('filterOrigin');
    const filterDestination = document.getElementById('filterDestination');
    const filterVisaType = document.getElementById('filterVisaType');
    
    if (searchInput) searchInput.value = '';
    if (filterOrigin) filterOrigin.value = '';
    if (filterDestination) filterDestination.value = '';
    if (filterVisaType) filterVisaType.value = '';
    
    handleFilter();
}

/**
 * Update "No routes found" message visibility
 */
function updateNoRoutesMessage() {
    const rows = document.querySelectorAll('.route-row');
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    const tbody = document.getElementById('routesTableBody');
    
    if (!tbody) return;
    
    // Check if there's already a "no routes" row
    let noRoutesRow = tbody.querySelector('.no-routes-row');
    
    if (visibleRows.length === 0 && rows.length > 0) {
        // Show "no routes found" message
        if (!noRoutesRow) {
            noRoutesRow = document.createElement('tr');
            noRoutesRow.className = 'no-routes-row';
            noRoutesRow.innerHTML = '<td colspan="7" class="px-6 py-4 text-center text-sm text-gray-500">No routes match the current filters</td>';
            tbody.appendChild(noRoutesRow);
        }
    } else {
        // Remove "no routes found" message
        if (noRoutesRow) {
            noRoutesRow.remove();
        }
    }
}

/**
 * Handle column sorting
 */
function handleSort(column) {
    // Toggle direction if same column
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    // Update sort indicators
    updateSortIndicators(column);
    
    // Sort table rows
    const tbody = document.getElementById('routesTableBody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('.route-row'));
    
    rows.sort((a, b) => {
        let aValue, bValue;
        
        switch (column) {
            case 'origin':
                aValue = a.getAttribute('data-origin') || '';
                bValue = b.getAttribute('data-origin') || '';
                break;
            case 'destination':
                aValue = a.getAttribute('data-destination') || '';
                bValue = b.getAttribute('data-destination') || '';
                break;
            case 'visa_type':
                aValue = a.getAttribute('data-visa') || '';
                bValue = b.getAttribute('data-visa') || '';
                break;
            case 'email':
                aValue = a.getAttribute('data-email') || '';
                bValue = b.getAttribute('data-email') || '';
                break;
            case 'created_at':
                aValue = a.querySelector('td:nth-child(5)')?.textContent?.trim() || '';
                bValue = b.querySelector('td:nth-child(5)')?.textContent?.trim() || '';
                break;
            default:
                return 0;
        }
        
        // Compare values
        if (aValue < bValue) return currentSort.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return currentSort.direction === 'asc' ? 1 : -1;
        return 0;
    });
    
    // Re-append sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Update sort indicators
 */
function updateSortIndicators(activeColumn) {
    const indicators = document.querySelectorAll('.sort-indicator');
    indicators.forEach(indicator => {
        indicator.textContent = '';
    });
    
    const activeHeader = document.querySelector(`[data-sort="${activeColumn}"] .sort-indicator`);
    if (activeHeader) {
        activeHeader.textContent = currentSort.direction === 'asc' ? ' ↑' : ' ↓';
    }
}

/**
 * Delete route with confirmation
 */
async function deleteRoute(routeId, routeDescription) {
    if (!confirm(`Are you sure you want to delete this route subscription?\n\n${routeDescription}\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        await API.deleteRoute(routeId);
        showMessage('Route deleted successfully', 'success');
        
        // Remove row from table
        const row = document.querySelector(`tr[data-route-id="${routeId}"]`);
        if (row) {
            row.style.transition = 'opacity 0.3s';
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                // Check if table is now empty
                const remainingRows = document.querySelectorAll('.route-row');
                if (remainingRows.length === 0) {
                    const tbody = document.getElementById('routesTableBody');
                    if (tbody) {
                        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-sm text-gray-500">No routes found</td></tr>';
                    }
                }
            }, 300);
        } else {
            // If row not found, reload page
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    } catch (error) {
        showMessage(`Error deleting route: ${error.message}`, 'error');
    }
}

/**
 * Show message to user
 */
function showMessage(message, type) {
    const container = document.getElementById('messageContainer');
    if (!container) return;
    
    const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
    const messageDiv = document.createElement('div');
    messageDiv.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg mb-2`;
    messageDiv.textContent = message;
    
    container.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

