/**
 * Sources list page functionality (search, filter, sort)
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
    const filterCountry = document.getElementById('filterCountry');
    const filterVisaType = document.getElementById('filterVisaType');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    if (filterCountry) {
        populateFilterDropdowns();
        filterCountry.addEventListener('change', handleFilter);
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
 * Populate filter dropdowns with unique values from sources
 */
function populateFilterDropdowns() {
    const rows = document.querySelectorAll('.source-row');
    const countrySet = new Set();
    
    rows.forEach(row => {
        const country = row.getAttribute('data-country');
        if (country) countrySet.add(country);
    });
    
    // Populate country dropdown
    const filterCountry = document.getElementById('filterCountry');
    if (filterCountry) {
        const sortedCountries = Array.from(countrySet).sort();
        sortedCountries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            filterCountry.appendChild(option);
        });
    }
}

/**
 * Handle search/filter input and dropdowns
 */
function handleFilter() {
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase().trim() || '';
    const filterCountry = document.getElementById('filterCountry')?.value || '';
    const filterVisaType = document.getElementById('filterVisaType')?.value || '';
    
    const rows = document.querySelectorAll('.source-row');
    
    rows.forEach(row => {
        const country = row.getAttribute('data-country') || '';
        const visaType = row.getAttribute('data-visa-type') || '';
        const url = row.getAttribute('data-url')?.toLowerCase() || '';
        const fetchType = row.getAttribute('data-fetch-type')?.toLowerCase() || '';
        
        // Check search term match
        const searchMatches = !searchTerm || 
            country.toLowerCase().includes(searchTerm) ||
            visaType.toLowerCase().includes(searchTerm) ||
            url.includes(searchTerm) ||
            fetchType.includes(searchTerm);
        
        // Check filter matches
        const countryMatches = !filterCountry || country === filterCountry;
        const visaMatches = !filterVisaType || visaType === filterVisaType;
        
        // Show row if all conditions match
        const matches = searchMatches && countryMatches && visaMatches;
        row.style.display = matches ? '' : 'none';
    });
    
    // Update "No sources found" message
    updateNoSourcesMessage();
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    const searchInput = document.getElementById('searchInput');
    const filterCountry = document.getElementById('filterCountry');
    const filterVisaType = document.getElementById('filterVisaType');
    
    if (searchInput) searchInput.value = '';
    if (filterCountry) filterCountry.value = '';
    if (filterVisaType) filterVisaType.value = '';
    
    handleFilter();
}

/**
 * Update "No sources found" message visibility
 */
function updateNoSourcesMessage() {
    const rows = document.querySelectorAll('.source-row');
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    const tbody = document.getElementById('sourcesTableBody');
    
    if (!tbody) return;
    
    // Check if there's already a "no sources" row
    let noSourcesRow = tbody.querySelector('.no-sources-row');
    
    if (visibleRows.length === 0 && rows.length > 0) {
        // Show "no sources found" message
        if (!noSourcesRow) {
            noSourcesRow = document.createElement('tr');
            noSourcesRow.className = 'no-sources-row';
            noSourcesRow.innerHTML = '<td colspan="8" class="px-6 py-4 text-center text-sm text-gray-500">No sources match the current filters</td>';
            tbody.appendChild(noSourcesRow);
        }
    } else {
        // Remove "no sources found" message
        if (noSourcesRow) {
            noSourcesRow.remove();
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
    const tbody = document.getElementById('sourcesTableBody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('.source-row'));
    
    rows.sort((a, b) => {
        let aValue, bValue;
        
        switch (column) {
            case 'country':
                aValue = a.getAttribute('data-country') || '';
                bValue = b.getAttribute('data-country') || '';
                break;
            case 'visa_type':
                aValue = a.getAttribute('data-visa-type') || '';
                bValue = b.getAttribute('data-visa-type') || '';
                break;
            case 'url':
                aValue = a.getAttribute('data-url') || '';
                bValue = b.getAttribute('data-url') || '';
                break;
            case 'fetch_type':
                aValue = a.getAttribute('data-fetch-type') || '';
                bValue = b.getAttribute('data-fetch-type') || '';
                break;
            case 'check_frequency':
                aValue = a.querySelector('td:nth-child(5)')?.textContent?.trim() || '';
                bValue = b.querySelector('td:nth-child(5)')?.textContent?.trim() || '';
                break;
            case 'last_checked':
                aValue = a.querySelector('td:nth-child(6)')?.textContent?.trim() || '';
                bValue = b.querySelector('td:nth-child(6)')?.textContent?.trim() || '';
                // Handle "Never" as earliest date
                if (aValue === 'Never') aValue = '';
                if (bValue === 'Never') bValue = '';
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
 * Delete source with confirmation and warning if has versions/changes
 */
async function deleteSource(sourceId, sourceDescription) {
    try {
        // Check if source has versions/changes
        const source = await API.getSource(sourceId);
        let hasVersions = false;
        let hasChanges = false;
        
        // Check for versions (we'll need to add this to API or check via detail endpoint)
        // For now, we'll show a generic warning
        const warningMessage = `Are you sure you want to delete this source?\n\n${sourceDescription}\n\nThis action cannot be undone.`;
        
        if (!confirm(warningMessage)) {
            return;
        }
        
        await API.deleteSource(sourceId);
        showMessage('Source deleted successfully', 'success');
        
        // Remove row from table
        const row = document.querySelector(`tr[data-source-id="${sourceId}"]`);
        if (row) {
            row.style.transition = 'opacity 0.3s';
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                // Check if table is now empty
                const remainingRows = document.querySelectorAll('.source-row');
                if (remainingRows.length === 0) {
                    const tbody = document.getElementById('sourcesTableBody');
                    if (tbody) {
                        tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-sm text-gray-500">No sources found</td></tr>';
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
        showMessage(`Error deleting source: ${error.message}`, 'error');
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

