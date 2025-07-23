/**
 * Environmental Data Dashboard JavaScript
 * 
 * This file contains the JavaScript code for the Environmental Data Dashboard.
 * It handles data loading, graph rendering, and user interactions.
 */

// Global variables
let days = 1;
let showP2 = true;
let showP3 = true;
let refreshInterval;

/**
 * Initialize the dashboard when the document is ready
 */
$(document).ready(function() {
    // Set default dates for export
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);
    
    $('#end-date').val(formatDate(today));
    $('#start-date').val(formatDate(weekAgo));
    
    // Load initial data
    refreshData();
    
    // Set up auto-refresh
    refreshInterval = setInterval(refreshData, 30000); // 30 seconds
    
    // Set up event handlers
    setupEventHandlers();
});

/**
 * Set up event handlers for user interactions
 */
function setupEventHandlers() {
    // Refresh button
    $('#refresh-btn').click(function() {
        refreshData();
    });
    
    // Time range dropdown
    $('.time-range').click(function(e) {
        e.preventDefault();
        days = $(this).data('days');
        $('#timeRangeDropdown').text('Time Range: ' + days + (days === 1 ? ' Day' : ' Days'));
        refreshGraphs();
    });
    
    // Device checkboxes
    $('#show-p2, #show-p3').change(function() {
        showP2 = $('#show-p2').prop('checked');
        showP3 = $('#show-p3').prop('checked');
        refreshGraphs();
    });
    
    // Export form
    $('#export-form').submit(function(e) {
        e.preventDefault();
        const deviceId = $('#device-select').val();
        const startDate = $('#start-date').val();
        const endDate = $('#end-date').val();
        
        window.location.href = `/api/export/csv/${deviceId}?start_date=${startDate}&end_date=${endDate}`;
    });
    
    // Handle tab changes
    $('#dataTabs button').on('shown.bs.tab', function (e) {
        // Resize graphs when tab is shown
        window.dispatchEvent(new Event('resize'));
    });
}

/**
 * Refresh all data on the dashboard
 */
function refreshData() {
    refreshLatestData();
    refreshConnectionStatus();
    refreshGraphs();
}

/**
 * Refresh the latest data table
 */
function refreshLatestData() {
    $.get('/api/latest-data-table', function(data) {
        $('#latest-data').html(data);
    }).fail(function() {
        $('#latest-data').html('<p class="text-danger">Failed to load latest data</p>');
    });
}

/**
 * Refresh the connection status table
 */
function refreshConnectionStatus() {
    $.get('/api/connection-status-table', function(data) {
        $('#connection-status').html(data);
    }).fail(function() {
        $('#connection-status').html('<p class="text-danger">Failed to load connection status</p>');
    });
}

/**
 * Refresh all graphs on the dashboard
 */
function refreshGraphs() {
    const parameters = ['temperature', 'humidity', 'absolute_humidity', 'co2', 'pressure', 'gas_resistance'];
    
    parameters.forEach(function(parameter) {
        refreshGraph(parameter);
    });
    
    refreshDashboard();
}

/**
 * Refresh a specific graph
 * 
 * @param {string} parameter - The parameter to refresh the graph for
 */
function refreshGraph(parameter) {
    $('#' + parameter + '-graph').html('<p class="loading">Loading graph...</p>');
    
    $.get(`/api/data/${parameter}?days=${days}&show_p2=${showP2}&show_p3=${showP3}`, function(data) {
        try {
            const graphData = JSON.parse(data);
            if (graphData.error) {
                $('#' + parameter + '-graph').html(`<p class="text-danger">${graphData.error}</p>`);
            } else {
                $('#' + parameter + '-graph').empty();
                Plotly.newPlot(parameter + '-graph', graphData.data, graphData.layout);
            }
        } catch (e) {
            $('#' + parameter + '-graph').html('<p class="text-danger">Error parsing graph data</p>');
            console.error('Error parsing graph data for ' + parameter, e);
        }
    }).fail(function(xhr, status, error) {
        $('#' + parameter + '-graph').html('<p class="text-danger">Failed to load graph</p>');
        console.error('Failed to load graph for ' + parameter, error);
    });
}

/**
 * Refresh the combined dashboard
 */
function refreshDashboard() {
    $('#dashboard-graph').html('<p class="loading">Loading dashboard...</p>');
    
    $.get(`/api/combined-dashboard?days=${days}&show_p2=${showP2}&show_p3=${showP3}`, function(data) {
        try {
            const graphData = JSON.parse(data);
            if (graphData.error) {
                $('#dashboard-graph').html(`<p class="text-danger">${graphData.error}</p>`);
            } else {
                $('#dashboard-graph').empty();
                Plotly.newPlot('dashboard-graph', graphData.data, graphData.layout);
            }
        } catch (e) {
            $('#dashboard-graph').html('<p class="text-danger">Error parsing dashboard data</p>');
            console.error('Error parsing dashboard data', e);
        }
    }).fail(function(xhr, status, error) {
        $('#dashboard-graph').html('<p class="text-danger">Failed to load dashboard</p>');
        console.error('Failed to load dashboard', error);
    });
}

/**
 * Format a date as YYYY-MM-DD
 * 
 * @param {Date} date - The date to format
 * @returns {string} The formatted date
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}