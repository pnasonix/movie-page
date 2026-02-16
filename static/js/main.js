// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
            // AJAX submit for comment form
            const commentForm = document.getElementById('commentForm');
            if (commentForm) {
                commentForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const textarea = commentForm.querySelector('textarea[name="comment"]');
                    const content = textarea.value.trim();
                    if (!content) return;
                    const movieId = window.movieId || commentForm.dataset.movieId || (typeof movie !== 'undefined' ? movie.id : null);
                    fetch('/comments', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ movie_id: movieId, content })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            textarea.value = '';
                            // Optionally reload comments or show success
                            alert('Bình luận đã được gửi!');
                        } else {
                            alert(data.error || 'Lỗi gửi bình luận');
                        }
                    })
                    .catch(() => alert('Lỗi gửi bình luận'));
                });
            }
        // Toggle comments dropdown icon
        const dropdownIcon = document.getElementById('commentDropdownIcon');
        const commentsList = document.querySelector('.comments-list');
        if (dropdownIcon && commentsList) {
            dropdownIcon.addEventListener('click', () => {
                commentsList.classList.toggle('collapsed');
                dropdownIcon.classList.toggle('active');
            });
        }
    console.log('DOM loaded, initializing mobile menu...');
    
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.animation = 'slideOut 0.3s';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // Mobile Menu Toggle
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileSidebar = document.getElementById('mobileSidebar');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mobileSearchToggle = document.getElementById('mobileSearchToggle');
    const mobileSearch = document.getElementById('mobileSearch');
    const mobileSearchClose = document.getElementById('mobileSearchClose');
    const mobileMoreToggle = document.getElementById('mobileMoreToggle');
    const mobileMoreDropdown = document.getElementById('mobileMoreDropdown');
    
    // Search elements
    const mobileSearchInput = document.getElementById('mobileSearchInput');
    const mobileSearchResults = document.getElementById('mobileSearchResults');
    const desktopSearchInput = document.getElementById('desktopSearchInput');
    const desktopSearchResults = document.getElementById('desktopSearchResults');

    console.log('Elements found:', {
        mobileMenuToggle: !!mobileMenuToggle,
        mobileSidebar: !!mobileSidebar,
        sidebarClose: !!sidebarClose,
        sidebarOverlay: !!sidebarOverlay,
        mobileSearchToggle: !!mobileSearchToggle,
        mobileSearch: !!mobileSearch,
        mobileSearchClose: !!mobileSearchClose,
        mobileMoreToggle: !!mobileMoreToggle,
        mobileMoreDropdown: !!mobileMoreDropdown
    });
    
    // Live Search functionality
    let searchTimeout = null;
    
    function performSearch(query, resultsContainer, isMobile) {
        if (!query || query.length < 2) {
            resultsContainer.innerHTML = '';
            return;
        }
        
        // Show loading
        resultsContainer.innerHTML = '<div class="' + (isMobile ? 'mobile-search-loading' : 'desktop-search-no-results') + '"><i class="fas fa-spinner fa-spin"></i> Đang tìm...</div>';
        
        fetch('/api/search?q=' + encodeURIComponent(query))
            .then(response => response.json())
            .then(movies => {
                if (movies.length === 0) {
                    resultsContainer.innerHTML = '<div class="' + (isMobile ? 'mobile-search-no-results' : 'desktop-search-no-results') + '">Không tìm thấy phim nào</div>';
                    return;
                }
                
                let html = '';
                movies.forEach(movie => {
                    const prefix = isMobile ? 'mobile' : 'desktop';
                    const posterUrl = movie.poster_url || '/static/images/no-poster.png';
                    const subtitleHtml = movie.subtitle ? `<div class="${prefix}-search-result-subtitle">${movie.subtitle}</div>` : '';
                    html += `
                        <a href="/movie/${movie.url_key}" class="${prefix}-search-result-item">
                            <img src="${posterUrl}" alt="${movie.title}" class="${prefix}-search-result-poster" onerror="this.src='/static/images/no-poster.png'">
                            <div class="${prefix}-search-result-info">
                                <div class="${prefix}-search-result-title">${movie.title}</div>
                                ${subtitleHtml}
                                <div class="${prefix}-search-result-meta">${movie.category || 'Chưa phân loại'} • ${movie.views} lượt xem</div>
                            </div>
                        </a>
                    `;
                });
                resultsContainer.innerHTML = html;
            })
            .catch(error => {
                console.error('Search error:', error);
                resultsContainer.innerHTML = '<div class="' + (isMobile ? 'mobile-search-no-results' : 'desktop-search-no-results') + '">Có lỗi xảy ra</div>';
            });
    }
    
    // Mobile search input handler
    if (mobileSearchInput && mobileSearchResults) {
        mobileSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value.trim(), mobileSearchResults, true);
            }, 300);
        });
    }
    
    // Desktop search input handler
    if (desktopSearchInput && desktopSearchResults) {
        desktopSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value.trim(), desktopSearchResults, false);
            }, 300);
        });
        
        // Close desktop results when clicking outside
        document.addEventListener('click', function(e) {
            const searchContainer = document.querySelector('.nav-search-desktop');
            if (searchContainer && !searchContainer.contains(e.target)) {
                desktopSearchResults.innerHTML = '';
            }
        });
        
        // Clear results on focus if empty
        desktopSearchInput.addEventListener('focus', function() {
            if (this.value.trim().length >= 2) {
                performSearch(this.value.trim(), desktopSearchResults, false);
            }
        });
    }

    // Mobile Menu
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Menu toggle clicked');
            if (mobileSidebar) {
                const wasActive = mobileSidebar.classList.contains('active');
                mobileSidebar.classList.toggle('active');
                const isActive = mobileSidebar.classList.contains('active');
                console.log('Sidebar is now:', isActive ? 'active' : 'inactive');
                
                if (sidebarOverlay) {
                    if (isActive) {
                        sidebarOverlay.classList.add('active');
                    } else {
                        sidebarOverlay.classList.remove('active');
                    }
                }
                document.body.style.overflow = isActive ? 'hidden' : '';
            } else {
                console.error('mobileSidebar not found!');
            }
        });
    } else {
        console.error('mobileMenuToggle not found!');
    }

    if (sidebarClose) {
        sidebarClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Sidebar close clicked');
            if (mobileSidebar) {
                mobileSidebar.classList.remove('active');
            }
            if (sidebarOverlay) {
                sidebarOverlay.classList.remove('active');
            }
            document.body.style.overflow = '';
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Overlay clicked');
            if (mobileSidebar) {
                mobileSidebar.classList.remove('active');
            }
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // Mobile Search Toggle
    if (mobileSearchToggle) {
        mobileSearchToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Search toggle clicked');
            if (mobileSearch) {
                const wasActive = mobileSearch.classList.contains('active');
                mobileSearch.classList.toggle('active');
                const isActive = mobileSearch.classList.contains('active');
                console.log('Search is now:', isActive ? 'active' : 'inactive');
                
                // Add/remove body class for CSS targeting
                document.body.classList.toggle('mobile-search-active', isActive);
                
                // Close more menu when opening search
                if (mobileMoreDropdown) {
                    mobileMoreDropdown.classList.remove('active');
                }
                
                if (isActive && !wasActive) {
                    const input = mobileSearch.querySelector('.mobile-search-input');
                    if (input) {
                        setTimeout(() => {
                            input.focus();
                            console.log('Input focused');
                        }, 150);
                    }
                }
            } else {
                console.error('mobileSearch not found!');
            }
        });
    } else {
        console.error('mobileSearchToggle not found!');
    }

    // Mobile Search Close button
    if (mobileSearchClose) {
        mobileSearchClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (mobileSearch) {
                mobileSearch.classList.remove('active');
                document.body.classList.remove('mobile-search-active');
                // Clear search results when closing
                if (mobileSearchResults) {
                    mobileSearchResults.innerHTML = '';
                }
                console.log('Search closed by close button');
            }
        });
    }

    // Mobile 3-dot More Menu Toggle
    if (mobileMoreToggle) {
        mobileMoreToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('More menu toggle clicked');
            if (mobileMoreDropdown) {
                mobileMoreDropdown.classList.toggle('active');
                
                // Close search when opening more menu
                if (mobileSearch) {
                    mobileSearch.classList.remove('active');
                }
            }
        });
    }

    // Close search when clicking outside (only if search is open)
    document.addEventListener('click', function(e) {
        if (mobileSearch && mobileSearch.classList.contains('active')) {
            if (!mobileSearch.contains(e.target) && 
                mobileSearchToggle && !mobileSearchToggle.contains(e.target)) {
                mobileSearch.classList.remove('active');
                // Clear search results when closing
                if (mobileSearchResults) {
                    mobileSearchResults.innerHTML = '';
                }
                console.log('Search closed by outside click');
            }
        }
        
        // Close more menu when clicking outside
        if (mobileMoreDropdown && mobileMoreDropdown.classList.contains('active')) {
            if (!mobileMoreDropdown.contains(e.target) && 
                mobileMoreToggle && !mobileMoreToggle.contains(e.target)) {
                mobileMoreDropdown.classList.remove('active');
                console.log('More menu closed by outside click');
            }
        }
    });

    // Touch events for mobile
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('touchend', function(e) {
            e.preventDefault();
            mobileMenuToggle.click();
        });
    }

    if (mobileSearchToggle) {
        mobileSearchToggle.addEventListener('touchend', function(e) {
            e.preventDefault();
            mobileSearchToggle.click();
        });
    }

    // Desktop Sidebar - Click Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const desktopSidebar = document.getElementById('desktopSidebar');
    
    function toggleSidebar() {
        if (!desktopSidebar) return;
        
        const isActive = desktopSidebar.classList.contains('active');
        
        // Sử dụng requestAnimationFrame để đảm bảo browser sẵn sàng render
        requestAnimationFrame(() => {
            if (isActive) {
                // Ẩn sidebar
                desktopSidebar.classList.remove('active');
                document.body.classList.remove('sidebar-open');
                localStorage.setItem('sidebarOpen', 'false');
            } else {
                // Hiện sidebar
                desktopSidebar.classList.add('active');
                document.body.classList.add('sidebar-open');
                localStorage.setItem('sidebarOpen', 'true');
            }
        });
    }
    
    if (sidebarToggle && desktopSidebar) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleSidebar();
        });
    }
    
    // Load sidebar state from localStorage
    const sidebarState = localStorage.getItem('sidebarOpen');
    if (sidebarState === 'true' && desktopSidebar) {
        desktopSidebar.classList.add('active');
        document.body.classList.add('sidebar-open');
    }
    
    
    
    // Sidebar Dropdown Toggle
    const sidebarDropdownToggle = document.querySelector('.sidebar-dropdown-toggle');
    const sidebarNavDropdown = document.querySelector('.sidebar-nav-dropdown');
    
    if (sidebarDropdownToggle && sidebarNavDropdown) {
        sidebarDropdownToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebarNavDropdown.classList.toggle('active');
        });
    }
    
    // Guest Avatar Click Toggle
    const guestAvatar = document.getElementById('guestAvatar');
    const userMenu = document.querySelector('.user-menu');
    
    if (guestAvatar && userMenu) {
        guestAvatar.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            userMenu.classList.toggle('active');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userMenu.contains(e.target)) {
                userMenu.classList.remove('active');
            }
        });
    }
});

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
