/**
 * Logix Authentication Guard
 * Protects admin pages from unauthorized access
 */

class AuthGuard {
    constructor() {
        this.loginUrl = '/auth/login';
        this.publicPaths = ['/auth/login', '/auth/signup', '/auth/reset-password'];
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        const token = this.getAuthToken();
        if (!token) {
            console.warn('🔒 No auth token found');
            return false;
        }

        // Check if token is expired (basic check)
        if (this.isTokenExpired(token)) {
            console.warn('🔒 Auth token expired');
            this.clearAuth();
            return false;
        }

        return true;
    }

    /**
     * Get authentication token from storage
     */
    getAuthToken() {
        return localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    }

    /**
     * Get refresh token from storage
     */
    getRefreshToken() {
        return localStorage.getItem('refreshToken') || sessionStorage.getItem('refreshToken');
    }

    /**
     * Get user data from storage
     */
    getUserData() {
        const userJson = localStorage.getItem('user') || sessionStorage.getItem('user');
        if (userJson) {
            try {
                return JSON.parse(userJson);
            } catch (e) {
                console.error('Failed to parse user data:', e);
                return null;
            }
        }
        return null;
    }

    /**
     * Check if token is expired (basic JWT decode)
     */
    isTokenExpired(token) {
        try {
            const payload = this.decodeJWT(token);
            if (!payload.exp) {
                return false; // No expiration set
            }

            const currentTime = Math.floor(Date.now() / 1000);
            return payload.exp < currentTime;
        } catch (e) {
            console.error('Failed to decode token:', e);
            return true; // Treat invalid tokens as expired
        }
    }

    /**
     * Decode JWT token (without verification)
     */
    decodeJWT(token) {
        try {
            const parts = token.split('.');
            if (parts.length !== 3) {
                throw new Error('Invalid token format');
            }

            const payload = parts[1];
            const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
            return JSON.parse(decoded);
        } catch (e) {
            throw new Error('Failed to decode JWT: ' + e.message);
        }
    }

    /**
     * Clear authentication data
     */
    clearAuth() {
        localStorage.removeItem('authToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        sessionStorage.removeItem('authToken');
        sessionStorage.removeItem('refreshToken');
        sessionStorage.removeItem('user');
    }

    /**
     * Redirect to login page
     */
    redirectToLogin(message = 'Please log in to continue') {
        console.log('🔒 Redirecting to login:', message);
        // Store current URL for redirect after login
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = this.loginUrl;
    }

    /**
     * Protect admin page - call this on page load
     */
    protect() {
        // Check if current page is public
        const currentPath = window.location.pathname;
        const isPublicPath = this.publicPaths.some(path => currentPath.startsWith(path));

        if (isPublicPath) {
            console.log('📖 Public page, no auth required');
            return true;
        }

        // Check authentication
        if (!this.isAuthenticated()) {
            console.warn('🔒 Authentication required, redirecting to login...');
            this.redirectToLogin();
            return false;
        }

        console.log('✅ Authentication verified');
        return true;
    }

    /**
     * Get authorization header for API requests
     */
    getAuthHeader() {
        const token = this.getAuthToken();
        return token ? `Bearer ${token}` : null;
    }

    /**
     * Make authenticated API request
     */
    async fetch(url, options = {}) {
        const authHeader = this.getAuthHeader();
        if (!authHeader) {
            throw new Error('No authentication token available');
        }

        const headers = {
            'Content-Type': 'application/json',
            'Authorization': authHeader,
            ...options.headers
        };

        try {
            const response = await fetch(url, { ...options, headers });

            // Handle 401 Unauthorized
            if (response.status === 401) {
                console.warn('🔒 Unauthorized request, clearing auth and redirecting...');
                this.clearAuth();
                this.redirectToLogin('Your session has expired');
                throw new Error('Unauthorized - session expired');
            }

            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Check if user has required role
     */
    hasRole(requiredRole) {
        const userData = this.getUserData();
        if (!userData || !userData.role) {
            return false;
        }

        if (Array.isArray(requiredRole)) {
            return requiredRole.includes(userData.role);
        }

        return userData.role === requiredRole;
    }

    /**
     * Show unauthorized message and redirect
     */
    showUnauthorized() {
        alert('You do not have permission to access this page.');
        window.location.href = '/admin';
    }
}

// Initialize auth guard
const authGuard = new AuthGuard();

// Automatically protect admin pages
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (window.location.pathname.startsWith('/admin')) {
            authGuard.protect();
        }
    });
} else {
    if (window.location.pathname.startsWith('/admin')) {
        authGuard.protect();
    }
}

// Make auth guard globally available
window.authGuard = authGuard;

