/**
 * Pagination Component
 * Displays pagination controls for paginated data
 */

import React from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  itemLabel?: string; // Optional label for items (default: "routes")
}

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  itemLabel = 'routes',
}) => {
  // Calculate range of items being displayed
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  // Generate page numbers to display
  const getPageNumbers = (): number[] => {
    const pages: number[] = [];
    const maxPagesToShow = 5;
    
    if (totalPages <= maxPagesToShow) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page, last page, and pages around current
      pages.push(1);
      
      if (currentPage > 3) {
        pages.push(-1); // Ellipsis marker
      }
      
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      if (currentPage < totalPages - 2) {
        pages.push(-1); // Ellipsis marker
      }
      
      pages.push(totalPages);
    }
    
    return pages;
  };

  const pageNumbers = getPageNumbers();

  if (totalPages <= 1) {
    // Don't show pagination if there's only one page or no items
    return (
      <div className="flex items-center justify-between py-4 border-t border-foreground">
        <p className="text-sm text-mutedForeground font-mono uppercase tracking-widest">
          Showing {startItem}-{endItem} of {totalItems} {itemLabel}
        </p>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between py-4 border-t-2 border-foreground">
      <p className="text-sm text-mutedForeground font-mono uppercase tracking-widest">
        Showing {startItem}-{endItem} of {totalItems} {itemLabel}
      </p>
      
      <div className="flex items-center space-x-2">
        {/* Previous Button */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Previous
        </button>

        {/* Page Numbers */}
        <div className="flex items-center space-x-1">
          {pageNumbers.map((page, index) => {
            if (page === -1) {
              // Ellipsis
              return (
                <span key={`ellipsis-${index}`} className="px-2 text-mutedForeground">
                  ...
                </span>
              );
            }

            return (
              <button
                key={page}
                onClick={() => onPageChange(page)}
                className={`px-4 py-2 border-2 border-foreground uppercase tracking-widest text-sm font-medium transition-colors duration-100 ${
                  currentPage === page
                    ? 'bg-foreground text-background'
                    : 'bg-background text-foreground hover:bg-foreground hover:text-background'
                }`}
              >
                {page}
              </button>
            );
          })}
        </div>

        {/* Next Button */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default Pagination;

