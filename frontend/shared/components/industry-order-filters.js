/**
 * Industry-Specific Order Filters Component
 * Provides filtering UI for orders by industry, type, and source
 */

class IndustryOrderFilters {
    constructor(containerId, onFilterChange) {
        this.container = document.getElementById(containerId);
        this.onFilterChange = onFilterChange;
        this.filters = {
            industry_category: null,
            order_type: null,
            order_source: null,
            status: null,
        };
        
        this.industryConfig = null;
        this.init();
    }
    
    async init() {
        console.log('🏭 Initializing industry order filters...');
        await this.loadIndustryConfig();
        this.render();
    }
    
    async loadIndustryConfig() {
        try {
            // Load industry categories
            const industryResponse = await window.authGuard.fetch('/api/v1/orders/industries');
            const industryData = await industryResponse.json();
            
            // Load order types
            const typesResponse = await window.authGuard.fetch('/api/v1/orders/types');
            const typesData = await typesResponse.json();
            
            // Load order sources
            const sourcesResponse = await window.authGuard.fetch('/api/v1/orders/sources');
            const sourcesData = await sourcesResponse.json();
            
            this.industryConfig = {
                industries: industryData.industries,
                orderTypes: typesData.order_types,
                orderSources: sourcesData.sources,
                allSources: sourcesData.all_sources,
            };
            
            console.log('✅ Industry configuration loaded:', this.industryConfig);
        } catch (error) {
            console.error('❌ Failed to load industry configuration:', error);
            // Use fallback configuration
            this.industryConfig = this.getFallbackConfig();
        }
    }
    
    getFallbackConfig() {
        return {
            industries: {
                "ecommerce": {name: "ecommerce", display_name: "E-commerce"},
                "retail": {name: "retail", display_name: "Retail Distribution"},
                "food_delivery": {name: "food_delivery", display_name: "Food Delivery"},
                "manufacturing": {name: "manufacturing", display_name: "Manufacturing"},
                "3pl": {name: "3pl", display_name: "3PL Services"}
            },
            orderTypes: {},
            orderSources: {
                "ecommerce": ["shopify", "woocommerce", "amazon_marketplace"],
                "retail": ["edi_system", "vendor_portal"],
                "food_delivery": ["uber_eats", "doordash", "grubhub"],
                "manufacturing": ["erp_system"],
                "3pl": ["client_portal", "api_integration"]
            },
            allSources: []
        };
    }
    
    render() {
        if (!this.container || !this.industryConfig) return;
        
        const html = `
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
                <div class="flex items-center gap-2 mb-4">
                    <span class="material-symbols-outlined text-primary">filter_alt</span>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Industry Filters</h3>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <!-- Industry Category Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Industry
                        </label>
                        <select id="filter-industry" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                            <option value="">All Industries</option>
                            ${Object.entries(this.industryConfig.industries).map(([key, industry]) => `
                                <option value="${key}">${industry.display_name}</option>
                            `).join('')}
                        </select>
                    </div>
                    
                    <!-- Order Type Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Order Type
                        </label>
                        <select id="filter-order-type" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                            <option value="">All Types</option>
                            ${Object.entries(this.industryConfig.orderTypes).map(([key, type]) => `
                                <option value="${key}">${this.formatTypeName(key)}</option>
                            `).join('')}
                        </select>
                    </div>
                    
                    <!-- Order Source Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Source
                        </label>
                        <select id="filter-order-source" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                            <option value="">All Sources</option>
                            ${this.industryConfig.allSources.map(source => `
                                <option value="${source}">${this.formatSourceName(source)}</option>
                            `).join('')}
                        </select>
                    </div>
                    
                    <!-- Status Filter -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Status
                        </label>
                        <select id="filter-status" class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                            <option value="">All Statuses</option>
                            <option value="pending">Pending</option>
                            <option value="confirmed">Confirmed</option>
                            <option value="processing">Processing</option>
                            <option value="shipped">Shipped</option>
                            <option value="delivered">Delivered</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                    </div>
                </div>
                
                <div class="flex justify-end gap-2 mt-4">
                    <button onclick="industryFilters.resetFilters()" class="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition">
                        Reset Filters
                    </button>
                    <button onclick="industryFilters.applyFilters()" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition">
                        Apply Filters
                    </button>
                </div>
            </div>
        `;
        
        this.container.innerHTML = html;
        this.attachEventListeners();
    }
    
    attachEventListeners() {
        const industrySelect = document.getElementById('filter-industry');
        const typeSelect = document.getElementById('filter-order-type');
        const sourceSelect = document.getElementById('filter-order-source');
        const statusSelect = document.getElementById('filter-status');
        
        // When industry changes, filter available types and sources
        if (industrySelect) {
            industrySelect.addEventListener('change', (e) => {
                this.updateDependentFilters(e.target.value);
            });
        }
    }
    
    updateDependentFilters(industry) {
        // Update order sources based on selected industry
        const sourceSelect = document.getElementById('filter-order-source');
        if (!sourceSelect) return;
        
        const currentValue = sourceSelect.value;
        
        if (industry && this.industryConfig.orderSources[industry]) {
            // Show only sources for selected industry
            const sources = this.industryConfig.orderSources[industry];
            sourceSelect.innerHTML = `
                <option value="">All Sources</option>
                ${sources.map(source => `
                    <option value="${source}">${this.formatSourceName(source)}</option>
                `).join('')}
            `;
        } else {
            // Show all sources
            sourceSelect.innerHTML = `
                <option value="">All Sources</option>
                ${this.industryConfig.allSources.map(source => `
                    <option value="${source}">${this.formatSourceName(source)}</option>
                `).join('')}
            `;
        }
        
        // Restore previous value if still valid
        if (currentValue) {
            sourceSelect.value = currentValue;
        }
    }
    
    applyFilters() {
        this.filters = {
            industry_category: document.getElementById('filter-industry')?.value || null,
            order_type: document.getElementById('filter-order-type')?.value || null,
            order_source: document.getElementById('filter-order-source')?.value || null,
            status: document.getElementById('filter-status')?.value || null,
        };
        
        console.log('🔍 Applying filters:', this.filters);
        
        if (this.onFilterChange) {
            this.onFilterChange(this.filters);
        }
    }
    
    resetFilters() {
        document.getElementById('filter-industry').value = '';
        document.getElementById('filter-order-type').value = '';
        document.getElementById('filter-order-source').value = '';
        document.getElementById('filter-status').value = '';
        
        this.filters = {
            industry_category: null,
            order_type: null,
            order_source: null,
            status: null,
        };
        
        console.log('🔄 Filters reset');
        
        if (this.onFilterChange) {
            this.onFilterChange(this.filters);
        }
    }
    
    formatTypeName(type) {
        return type.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    formatSourceName(source) {
        if (source === '3pl') return '3PL';
        return source.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    getActiveFilters() {
        return Object.entries(this.filters)
            .filter(([key, value]) => value !== null && value !== '')
            .reduce((obj, [key, value]) => ({...obj, [key]: value}), {});
    }
}

// Initialize global instance when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 Industry Order Filters component ready');
});

