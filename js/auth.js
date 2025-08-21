/**
 * Authentication utilities for the GitHub Pages frontend
 */

class AuthManager {
    constructor() {
        this.user = null;
        this.isAuthenticated = false;
        this.init();
    }

    init() {
        // Check if user is logged in from previous session
        this.loadUserFromStorage();
        this.updateUI();

        // Check session validity with API
        if (this.isAuthenticated) {
            this.validateSession();
        } else {
            this.showLoginBanner();
        }
    }

    loadUserFromStorage() {
        try {
            const userData = localStorage.getItem(APP_CONFIG.STORAGE_KEYS.USER_DATA);
            if (userData) {
                this.user = JSON.parse(userData);
                this.isAuthenticated = true;
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            this.clearUserData();
        }
    }

    saveUserToStorage(userData) {
        try {
            localStorage.setItem(APP_CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
            this.user = userData;
            this.isAuthenticated = true;
        } catch (error) {
            console.error('Error saving user data:', error);
        }
    }

    clearUserData() {
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER_DATA);
        localStorage.removeItem(APP_CONFIG.STORAGE_KEYS.USER_TOKEN);
        this.user = null;
        this.isAuthenticated = false;
    }

    async login(username, password) {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.AUTH.LOGIN), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // Important for session cookies
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                this.saveUserToStorage(data.user);
                this.updateUI();
                return { success: true, user: data.user };
            } else {
                return { success: false, error: data.error || 'Login failed' };
            }
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: 'Network error - please check API connection' };
        }
    }

    async logout() {
        try {
            // Call API logout endpoint
            await fetch(getApiUrl(API_CONFIG.ENDPOINTS.AUTH.LOGOUT), {
                method: 'POST',
                credentials: 'include'
            });
        } catch (error) {
            console.error('Logout API error:', error);
        } finally {
            // Clear local data regardless of API response
            this.clearUserData();
            this.updateUI();
            this.showLoginBanner();
        }
    }

    async validateSession() {
        try {
            const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.AUTH.PROFILE), {
                credentials: 'include'
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Update user data from server
                    this.saveUserToStorage(data.user);
                    return true;
                }
            }

            // Session invalid, clear local data
            this.clearUserData();
            this.updateUI();
            return false;
        } catch (error) {
            console.error('Session validation error:', error);
            return false;
        }
    }

    updateUI() {
        const loginStatus = document.getElementById('loginStatus');
        const userMenu = document.getElementById('userMenu');
        const userName = document.getElementById('userName');
        const loginBanner = document.getElementById('loginBanner');
        const configInfo = document.getElementById('configInfo');

        if (this.isAuthenticated && this.user) {
            // Show user menu, hide login link
            if (loginStatus) loginStatus.style.display = 'none';
            if (userMenu) userMenu.style.display = 'block';
            if (userName) userName.textContent = this.user.full_name || this.user.username;
            if (loginBanner) loginBanner.style.display = 'none';

            // Show configuration info
            if (configInfo) {
                configInfo.style.display = 'block';
                this.updateConfigInfo();
            }
        } else {
            // Show login link, hide user menu
            if (loginStatus) loginStatus.style.display = 'block';
            if (userMenu) userMenu.style.display = 'none';
            if (configInfo) configInfo.style.display = 'none';
        }
    }

    updateConfigInfo() {
        const configContent = document.getElementById('configContent');
        if (configContent && this.user) {
            configContent.innerHTML = `
                <div class="small">
                    <strong>User:</strong> ${this.user.username}<br>
                    <strong>Role:</strong> ${this.user.role}<br>
                    <strong>Organization:</strong> ${this.user.organization_name || 'Default'}<br>
                    <small class="text-muted">
                        Your personalized settings are active.<br>
                        <a href="config.html" class="text-decoration-none">Customize Settings</a>
                    </small>
                </div>
            `;
        }
    }

    showLoginBanner() {
        const loginBanner = document.getElementById('loginBanner');
        if (loginBanner && !this.isAuthenticated) {
            loginBanner.style.display = 'block';
        }
    }

    // Get current user data
    getCurrentUser() {
        return this.user;
    }

    // Check if user has specific role
    hasRole(role) {
        return this.user && this.user.role === role;
    }

    // Check if user is admin
    isAdmin() {
        return this.hasRole('super_admin') || this.hasRole('org_admin');
    }

    // Get authorization headers for API calls
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        // For session-based auth, credentials: 'include' is more important than headers
        return headers;
    }

    // Make authenticated API call
    async apiCall(url, options = {}) {
        const defaultOptions = {
            credentials: 'include',
            headers: this.getAuthHeaders()
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, mergedOptions);

            // Check if unauthorized (session expired)
            if (response.status === 401) {
                this.clearUserData();
                this.updateUI();
                throw new Error('Session expired - please log in again');
            }

            return response;
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }
}

// Global auth manager instance
window.authManager = new AuthManager();

// Global logout function for navbar
function logout() {
    authManager.logout().then(() => {
        // Redirect to home page after logout
        if (window.location.pathname !== '/index.html' && window.location.pathname !== '/') {
            window.location.href = 'index.html';
        }
    });
}
