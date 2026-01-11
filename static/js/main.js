// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
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

    console.log('Elements found:', {
        mobileMenuToggle: !!mobileMenuToggle,
        mobileSidebar: !!mobileSidebar,
        sidebarClose: !!sidebarClose,
        sidebarOverlay: !!sidebarOverlay,
        mobileSearchToggle: !!mobileSearchToggle,
        mobileSearch: !!mobileSearch
    });

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

    // Close search when clicking outside (only if search is open)
    document.addEventListener('click', function(e) {
        if (mobileSearch && mobileSearch.classList.contains('active')) {
            if (!mobileSearch.contains(e.target) && 
                mobileSearchToggle && !mobileSearchToggle.contains(e.target)) {
                mobileSearch.classList.remove('active');
                console.log('Search closed by outside click');
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
