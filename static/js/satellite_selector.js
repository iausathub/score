/**
 * SatelliteSelector - Interactive satellite selection component
 * Handles constellation and individual satellite selection for data visualization
 */
class SatelliteSelector {
    // Constants
    static FALLBACK_CONSTELLATION = {
        other: {
            name: window.ConstellationConfig?.getName('other') || 'Other',
            color: 'secondary',
            count: 0,
            satellites: []
        }
    };

    // Bootstrap CSS color classes for badges (not chart colors)
    static BOOTSTRAP_COLOR_CLASSES = {
        starlink: 'primary',
        kuiper: 'accent1',
        qianfan: 'accent2',
        spacemobile: 'accent3',
        oneweb: 'danger',
        other: 'secondary'
    };

    static FILTER_KEYS = [
        'filterStartDate', 'filterEndDate',
        'filterMinMag', 'filterMaxMag',
        'filterMinSatElev', 'filterMaxSatElev',
        'filterMinSolarElev', 'filterMaxSolarElev'
    ];

    /**
     * Initialize the satellite selector
     * @param {Object} options - Configuration options
     * @param {Object} options.constellations - Constellation data
     * @param {number} options.defaultVisibleCount - Default number of satellites to show
     * @param {string} options.defaultExpandedGroup - Default group to expand
     */
    constructor(options = {}) {
        // Configuration with defaults
        this.config = {
            defaultVisibleCount: 20,
            defaultExpandedGroup: 'starlink',
            ...options
        };

        // Constellation data - will be loaded from API
        this.constellations = {};

        // State management
        this.state = {
            selectedConstellations: new Set(),
            selectedSatellites: new Set(),
            searchQuery: '',
            expandedGroups: new Set([this.config.defaultExpandedGroup]),
            visibleCounts: {}
        };

        // DOM element cache
        this.elements = {};
        this.cardBody = null;

        this.init();
    }

    async init() {
        this.cacheElements();
        this.setupEventListeners();

        await this.loadConstellationData();

        this.renderConstellationMode();
        this.renderCustomMode();
        this.updateSelectionText();

        // Initialize satellite names display
        const satelliteNamesContainer = document.getElementById('satellite-names');
        if (satelliteNamesContainer) {
            satelliteNamesContainer.innerHTML = '<p class="text-muted small text-center">Select satellites and click Apply to see the list</p>';
        }
    }

    /**
     * Cache frequently used DOM elements
     */
    cacheElements() {
        this.elements = {
            searchInput: document.getElementById('search-input'),
            selectionText: document.getElementById('selection-text'),
            constellationsList: document.getElementById('constellations-list'),
            customList: document.getElementById('custom-list'),
            applyButton: document.getElementById('apply-selection'),
            applyButtonFilters: document.getElementById('apply-selection-filters'),
            clearSelectionsButton: document.getElementById('clear-selections'),
            clearFiltersButton: document.getElementById('clear-filters')
        };
        this.cardBody = document.getElementById('charts-container')?.parentElement;
    }

    /**
     * Load constellation data from the API
     */
    async loadConstellationData() {
        try {
            const response = await fetch('/api/satellite-data/');
            const data = await response.json();

            if (data.success) {
                this.constellations = this.addColorMapping(data.constellations);
            } else {
                console.error('Failed to load constellation data:', data.error);
                this.constellations = SatelliteSelector.FALLBACK_CONSTELLATION;
            }
        } catch (error) {
            console.error('Error loading constellation data:', error);
            this.constellations = SatelliteSelector.FALLBACK_CONSTELLATION;
        }
    }

    /**
     * Add naming and color mapping to constellation data from API
     * @param {Object} constellations - Raw constellation data from API
     * @returns {Object} Constellations with naming and color mapping added
     */
    addColorMapping(constellations) {
        const result = {};
        for (const [id, data] of Object.entries(constellations)) {
            result[id] = {
                ...data,
                name: window.ConstellationConfig.getName(id),
                color: SatelliteSelector.BOOTSTRAP_COLOR_CLASSES[id] || SatelliteSelector.BOOTSTRAP_COLOR_CLASSES.other
            };
        }
        return result;
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        try {
            // Mode tabs
            document.querySelectorAll('.mode-tab').forEach(tab => {
                tab.addEventListener('click', (e) => this.handleModeSwitch(e));
            });

            // Search input
            if (this.elements.searchInput) {
                this.elements.searchInput.addEventListener('input', (e) => this.handleSearch(e));
            }

            // Apply buttons
            if (this.elements.applyButton) {
                this.elements.applyButton.addEventListener('click', () => this.applySelection());
            }
            if (this.elements.applyButtonFilters) {
                this.elements.applyButtonFilters.addEventListener('click', () => this.applySelection());
            }

            // Clear selections button
            if (this.elements.clearSelectionsButton) {
                this.elements.clearSelectionsButton.addEventListener('click', () => this.clearSelections());
            }

            // Clear filters button
            if (this.elements.clearFiltersButton) {
                this.elements.clearFiltersButton.addEventListener('click', () => this.clearFilters());
            }

            SatelliteSelector.FILTER_KEYS.forEach(key => {
                const elementId = key.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, '');
                const input = document.getElementById(elementId);
                if (input) {
                    input.addEventListener('input', () => this.updateSelectionText());
                }
            });

            if (this.elements.customList) {
                this.elements.customList.addEventListener('click', (e) => {
                    const groupHeader = e.target.closest('.group-header');
                    const loadMoreBtn = e.target.closest('.load-more-btn');

                    if (groupHeader) this.toggleGroup(groupHeader.dataset.group);
                    if (loadMoreBtn) this.loadMore(loadMoreBtn.dataset.group);
                });

                this.elements.customList.addEventListener('change', (e) => {
                    if (e.target.classList.contains('satellite-checkbox')) {
                        this.toggleSatellite(e.target.dataset.satellite);
                    }
                });
            }
        } catch (error) {
            console.error('Error setting up event listeners:', error);
        }
    }

    /**
     * Handle mode switch events
     * @param {Event} event - Click event
     */
    handleModeSwitch(event) {
        const mode = event.target.dataset.mode;
        if (!mode) return;

        this.switchMode(mode);
    }

    /**
     * Handle search input events
     * @param {Event} event - Input event
     */
    handleSearch(event) {
        this.state.searchQuery = event.target.value;
        this.state.visibleCounts = {};
        this.renderCustomMode();
    }

    /**
     * Switch between constellation and custom modes
     * @param {string} mode - Mode to switch to ('constellations' or 'custom')
     */
    switchMode(mode) {
        try {
            // Hide all mode content
            document.querySelectorAll('.mode-content').forEach(el => {
                el.classList.add('d-none');
            });

            // Show selected mode
            const targetMode = document.getElementById(`${mode}-mode`);
            if (targetMode) {
                targetMode.classList.remove('d-none');
            }

            // Update tab states
            document.querySelectorAll('.mode-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            const activeTab = document.querySelector(`[data-mode="${mode}"]`);
            if (activeTab) {
                activeTab.classList.add('active');
            }

            // Reset search when switching to custom mode
            if (mode === 'custom' && this.elements.searchInput) {
                this.state.searchQuery = '';
                this.elements.searchInput.value = '';
            }
        } catch (error) {
            console.error('Error switching mode:', error);
        }
    }

    /**
     * Render constellation selection mode
     */
    renderConstellationMode() {
        if (!this.elements.constellationsList) return;

        try {
            // Sort constellations with 'other' at the end
            const sortedEntries = Object.entries(this.constellations).sort(([idA], [idB]) => {
                if (idA === 'other') return 1;
                if (idB === 'other') return -1;
                return 0;
            });

            const html = sortedEntries
                .map(([id, constellation]) => this.createConstellationItem(id, constellation))
                .join('');

            this.elements.constellationsList.innerHTML = html;
            this.attachConstellationEventListeners();
        } catch (error) {
            console.error('Error rendering constellation mode:', error);
        }
    }

    /**
     * Create HTML for a constellation item
     * @param {string} id - Constellation ID
     * @param {Object} constellation - Constellation data
     * @returns {string} HTML string
     */
    createConstellationItem(id, constellation) {
        const checked = this.state.selectedConstellations.has(id) ? 'checked' : '';
        const count = constellation.count.toLocaleString();

        return `
            <label class="constellation-item d-flex align-items-start gap-3 p-3 rounded cursor-pointer">
                <input
                    type="checkbox"
                    class="constellation-checkbox mt-1"
                    data-id="${this.escapeHtml(id)}"
                    ${checked}
                >
                <div class="flex-grow-1">
                    <div class="fw-medium">${this.escapeHtml(constellation.name)}</div>
                    <small class="text-muted">${count} satellites in SCORE</small>
                </div>
                <span class="badge bg-${constellation.color} constellation-badge">
                    ${count}
                </span>
            </label>
        `;
    }

    /**
     * Attach event listeners to constellation checkboxes
     */
    attachConstellationEventListeners() {
        document.querySelectorAll('.constellation-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const id = e.target.dataset.id;
                if (id) {
                    this.toggleConstellation(id);
                }
            });
        });
    }

    /**
     * Escape HTML
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    renderCustomMode() {
        if (!this.elements.customList) return;

        const list = this.elements.customList;
        const filtered = this.getFilteredConstellations();

        if (Object.keys(filtered).length === 0) {
            list.innerHTML = '<p class="text-muted text-center p-3 small">No satellites match your search</p>';
            return;
        }

        list.innerHTML = Object.entries(filtered).map(([groupId, { satellites, total }]) => {
            const isExpanded = this.state.expandedGroups.has(groupId);
            const visibleCount = this.state.visibleCounts[groupId] || this.config.defaultVisibleCount;
            const visibleSatellites = satellites.slice(0, visibleCount);
            const hasMore = satellites.length > visibleCount;
            const collapsedClass = !isExpanded ? 'collapsed' : '';
            const searchText = this.state.searchQuery ? 'found' : 'available';

            const satelliteItems = visibleSatellites.map(sat => {
                const satChecked = this.state.selectedSatellites.has(sat) ? 'checked' : '';
                return `
                    <div class="satellite-item">
                        <label class="d-flex align-items-center">
                            <input
                                type="checkbox"
                                class="satellite-checkbox"
                                data-satellite="${sat}"
                                ${satChecked}
                            >
                            <span class="satellite-name ms-2">${sat}</span>
                        </label>
                    </div>
                `;
            }).join('');

            const loadMoreBtn = hasMore ? `
                <button class="load-more-btn" data-group="${groupId}">
                    Load more (${this.constellations[groupId].count - visibleCount} remaining)
                </button>
            ` : '';

            const groupItems = isExpanded ? `
                <div class="group-items">
                    ${satelliteItems}
                    ${loadMoreBtn}
                </div>
            ` : '';

            return `
                <div class="constellation-group">
                    <button class="group-header ${collapsedClass}" data-group="${groupId}">
                        <span class="chevron"><i class="fas fa-chevron-down"></i></span>
                        <span class="fw-medium">${this.constellations[groupId].name}</span>
                        <span class="text-muted float-end small">${this.constellations[groupId].count} ${searchText}</span>
                    </button>
                    ${groupItems}
                </div>
            `;
        }).join('');
        // Event listeners are handled by event delegation in setupEventListeners()
    }

    getFilteredConstellations() {
        if (!this.state.searchQuery) {
            return Object.fromEntries(
                Object.entries(this.constellations).map(([id, data]) => [
                    id,
                    { satellites: data.satellites, total: data.count }
                ])
            );
        }

        const filtered = {};
        Object.entries(this.constellations).forEach(([id, constellation]) => {
            const matches = constellation.satellites.filter(sat =>
                sat.toLowerCase().includes(this.state.searchQuery.toLowerCase())
            );
            if (matches.length > 0) {
                filtered[id] = { satellites: matches, total: constellation.count };
            }
        });
        return filtered;
    }

    /**
     * Toggle constellation selection
     * @param {string} id - Constellation ID
     */
    toggleConstellation(id) {
        if (this.state.selectedConstellations.has(id)) {
            this.state.selectedConstellations.delete(id);
        } else {
            this.state.selectedConstellations.add(id);
        }
        this.updateSelectionText();
    }

    /**
     * Toggle group expansion
     * @param {string} id - Group ID
     */
    toggleGroup(id) {
        if (this.state.expandedGroups.has(id)) {
            this.state.expandedGroups.delete(id);
        } else {
            this.state.expandedGroups.add(id);
        }
        this.renderCustomMode();
    }

    /**
     * Toggle individual satellite selection
     * @param {string} satellite - Satellite name
     */
    toggleSatellite(satellite) {
        if (this.state.selectedSatellites.has(satellite)) {
            this.state.selectedSatellites.delete(satellite);
        } else {
            this.state.selectedSatellites.add(satellite);
        }
        this.updateSelectionText();
    }

    /**
     * Load more satellites for a group
     * @param {string} groupId - Group ID
     */
    loadMore(groupId) {
        this.state.visibleCounts[groupId] = (this.state.visibleCounts[groupId] || this.config.defaultVisibleCount) + this.config.defaultVisibleCount;
        this.renderCustomMode();
    }

    /**
     * Calculate total selected satellites from constellations
     * @returns {number} Total constellation satellites
     */
    getConstellationTotal() {
        return Array.from(this.state.selectedConstellations).reduce(
            (sum, id) => sum + (this.constellations[id]?.count || 0),
            0
        );
    }

    /**
     * Update the selection text display and apply button state
     */
    updateSelectionText() {
        if (!this.elements.selectionText) return;

        const total = this.getTotalSelected();
        const text = total === 0
            ? 'Choose constellations or specific satellites'
            : `${total.toLocaleString()} ${total === 1 ? 'object' : 'objects'} selected`;

        this.elements.selectionText.textContent = text;

        // Enable apply buttons if satellites are selected OR filters have values
        const hasFilters = this.hasAnyFilters();
        const isDisabled = total === 0 && !hasFilters;
        if (this.elements.applyButton) {
            this.elements.applyButton.disabled = isDisabled;
        }
        if (this.elements.applyButtonFilters) {
            this.elements.applyButtonFilters.disabled = isDisabled;
        }
    }

    /**
     * Check if any filter has a value
     * @returns {boolean} True if any filter is set
     */
    hasAnyFilters() {
        const filters = this.getFilterValues();
        return Object.values(filters).some(value => {
            // Check if value exists and is not empty
            return value !== null && value !== undefined && value !== '';
        });
    }

    /**
     * Apply the current selection and update charts
     */
    async applySelection() {
        try {
            await this.loadObservationsForCharts();
        } catch (error) {
            console.error('Error applying selection:', error);
        }
    }

    /**
     * Get current filter values
     * @returns {Object} Filter values
     */
    getFilterValues() {
        const getValue = (id) => {
            const element = document.getElementById(id);
            const val = element?.value;
            return (val && val.trim() !== '') ? val : null;
        };

        return {
            startDate: getValue('filter-start-date'),
            endDate: getValue('filter-end-date'),
            minMag: getValue('filter-min-mag'),
            maxMag: getValue('filter-max-mag'),
            minSatElev: getValue('filter-min-sat-elev'),
            maxSatElev: getValue('filter-max-sat-elev'),
            minSolarElev: getValue('filter-min-solar-elev'),
            maxSolarElev: getValue('filter-max-solar-elev')
        };
    }

    /**
     * Clear all satellite selections (constellations and custom)
     */
    clearSelections() {
        // Clear both constellation and custom satellite selections
        this.state.selectedConstellations.clear();
        this.state.selectedSatellites.clear();

        // Re-render both modes to update the UI
        this.renderConstellationMode();
        this.renderCustomMode();

        // Update the selection text display
        this.updateSelectionText();
    }

    /**
     * Clear all filters
     */
    clearFilters() {
        SatelliteSelector.FILTER_KEYS.forEach(key => {
            const elementId = key.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, '');
            const element = document.getElementById(elementId);
            if (element) {
                element.value = '';
            }
        });

        // Update button states after clearing
        this.updateSelectionText();
    }

    /**
     * Load observations for selected satellites and update charts
     */
    async loadObservationsForCharts() {
        try {
            this.showLoading();

            const params = new URLSearchParams();

            // Add selected constellations
            this.state.selectedConstellations.forEach(constellation => {
                params.append('constellations[]', constellation);
            });

            // Add selected individual satellites
            this.state.selectedSatellites.forEach(satellite => {
                params.append('satellites[]', satellite);
            });

            // Add filters
            const filters = this.getFilterValues();
            if (filters.startDate) params.append('start_date', filters.startDate);
            if (filters.endDate) params.append('end_date', filters.endDate);
            if (filters.minMag) params.append('min_mag', filters.minMag);
            if (filters.maxMag) params.append('max_mag', filters.maxMag);
            if (filters.minSatElev) params.append('min_sat_elev', filters.minSatElev);
            if (filters.maxSatElev) params.append('max_sat_elev', filters.maxSatElev);
            if (filters.minSolarElev) params.append('min_solar_elev', filters.minSolarElev);
            if (filters.maxSolarElev) params.append('max_solar_elev', filters.maxSolarElev);

            const response = await fetch(`/api/observations/?${params.toString()}`);
            const data = await response.json();

            console.log('API Response:', {
                success: data.success,
                observationCount: data.observations?.length || 0,
                filters: this.getFilterValues(),
                selectedConstellations: Array.from(this.state.selectedConstellations),
                selectedSatellites: Array.from(this.state.selectedSatellites)
            });

            if (data.success) {
                // Update the observations data element that charts read from
                this.updateObservationsDataElement(data.observations);

                // Update satellite names list
                this.updateSatelliteNamesList(data.observations);

                if (data.observations.length > 0) {
                    console.log(`Showing charts with ${data.observations.length} observations`);
                    // Show the charts and controls first (so Chart.js can calculate sizes)
                    this.showCharts();

                    // Wait to ensure DOM is updated before charts read it
                    setTimeout(() => {
                        this.initializeAndUpdateCharts();
                        this.hideLoading();
                    }, 50);
                } else {
                    console.log('No observations returned - hiding charts');
                    // Hide charts if no observations
                    this.hideCharts();
                    this.hideLoading();
                }
            } else {
                this.hideLoading();
                console.error('Failed to load observations:', data.error);
            }

        } catch (error) {
            this.hideLoading();
            console.error('Error loading observations for charts:', error);
        }
    }

    /**
     * Get theme-appropriate overlay color
     * @returns {string} RGBA color string
     */
    getOverlayColor() {
        const theme = window.ConstellationConfig.getCurrentTheme();
        return theme === 'dark' ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.7)';
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        if (!this.cardBody) return;

        this.cardBody.style.position = 'relative';

        // Create/show overlay
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.style.cssText = `position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 999; backdrop-filter: blur(2px);`;
            this.cardBody.appendChild(overlay);
        }
        overlay.style.background = this.getOverlayColor();
        overlay.style.display = 'block';

        // Create/show loading indicator
        let loading = document.getElementById('loading-indicator');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'loading-indicator';
            loading.className = 'text-center p-5';
            loading.style.cssText = 'position: absolute; top: 2rem; left: 50%; transform: translateX(-50%); z-index: 1001; background: var(--bs-body-bg); padding: 2rem; border-radius: 0.5rem; box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.15);';
            loading.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3 mb-0 text-muted">Loading observations...</p>
            `;
            this.cardBody.appendChild(loading);
        }
        loading.style.display = 'block';
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        ['loading-indicator', 'loading-overlay'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
    }

    /**
     * Show the charts and controls
     */
    showCharts() {
        ['charts-container', 'plots-container', 'chart-controls'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.remove('d-none');
        });
    }

    /**
     * Hide the charts and controls
     */
    hideCharts() {
        ['charts-container', 'plots-container', 'chart-controls'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('d-none');
        });
    }

    /**
     * Initialize charts if needed and update them with new data
     */
    initializeAndUpdateCharts() {
        const updateCharts = () => {
            if (typeof window.updateCharts === 'function') {
                try {
                    window.updateCharts();
                } catch (error) {
                    console.error('Error calling updateCharts():', error);
                }
                return true;
            }
            return false;
        };

        // Try immediately, or retry once after short delay
        if (!updateCharts()) {
            setTimeout(updateCharts, 200);
        }
    }

    /**
     * Update the observations data element that charts read from
     * @param {Array} observations - New observation data
     */
    updateObservationsDataElement(observations) {
        const el = document.getElementById('observations-data');
        if (el) {
            el.textContent = JSON.stringify(observations);
        }
    }

    /**
     * Update the satellite names list display
     * @param {Array} observations - Observation data
     */
    updateSatelliteNamesList(observations) {
        const container = document.getElementById('satellite-names');
        if (!container) return;

        // Extract unique satellite names
        const uniqueSatellites = new Set();
        observations.forEach(obs => {
            const satName = obs.satellite_name || obs.satellite || obs.sat_name || obs.name;
            if (satName) {
                uniqueSatellites.add(satName);
            }
        });

        // Sort alphabetically and create simple list
        const sortedSatellites = Array.from(uniqueSatellites).sort();

        if (sortedSatellites.length === 0) {
            container.innerHTML = '<p class="text-muted small">No satellites</p>';
            return;
        }

        const html = `
            <p class="text-muted small mb-2"><strong>${sortedSatellites.length}</strong> satellites:</p>
            <div class="satellite-list">
                ${sortedSatellites.map(sat => `<div>${this.escapeHtml(sat)}</div>`).join('')}
            </div>
        `;

        container.innerHTML = html;
    }

    /**
     * Get current selection state
     * @returns {Object} Current selection state
     */
    getSelection() {
        return {
            selectedConstellations: Array.from(this.state.selectedConstellations),
            selectedSatellites: Array.from(this.state.selectedSatellites),
            total: this.getTotalSelected()
        };
    }

    /**
     * Get total number of selected satellites
     * @returns {number} Total selected count
     */
    getTotalSelected() {
        return this.getConstellationTotal() + this.state.selectedSatellites.size;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    try {
        const requiredElements = [
            'constellations-list',
            'custom-list',
            'search-input',
            'selection-text',
            'apply-selection'
        ];

        const missingElements = requiredElements.filter(id => !document.getElementById(id));

        if (missingElements.length > 0) {
            console.error('SatelliteSelector: Missing required elements:', missingElements);
            return;
        }

        window.satelliteSelector = new SatelliteSelector();
    } catch (error) {
        console.error('Error initializing SatelliteSelector:', error);
    }
});
