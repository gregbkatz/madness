/**
 * Win Percentage Chart - Shows timeline of win percentages for all users
 */
document.addEventListener('DOMContentLoaded', function () {
    // No need to manually register the annotation plugin - it will auto-register
    // Chart.register(ChartAnnotation);

    // Chart instance
    let winChart = null;

    // Keep track of all timeline data
    let allTimelineData = [];

    // Current timeline index
    let currentTimelineIndex = 0;

    // Colors for user lines (can be expanded)
    const colors = [
        'rgba(54, 162, 235, 1)',   // blue
        'rgba(255, 99, 132, 1)',   // red
        'rgba(75, 192, 192, 1)',   // green
        'rgba(255, 159, 64, 1)',   // orange
        'rgba(153, 102, 255, 1)',  // purple
        'rgba(255, 205, 86, 1)',   // yellow
        'rgba(201, 203, 207, 1)',  // grey
        'rgba(54, 72, 155, 1)',    // dark blue
        'rgba(192, 75, 75, 1)',    // dark red
        'rgba(46, 139, 87, 1)',    // sea green
        'rgba(255, 127, 80, 1)',   // coral
        'rgba(138, 43, 226, 1)',   // blue violet
        'rgba(189, 183, 107, 1)',  // dark khaki
        'rgba(112, 128, 144, 1)'   // slate grey
    ];

    // Initialize the chart
    function initializeChart() {
        const ctx = document.getElementById('winPercentageChart');

        if (!ctx) {
            console.error('Chart canvas element not found');
            return;
        }

        // Create empty chart - we'll populate with data later
        winChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false, // Disable animations
                transitions: {
                    active: {
                        animation: {
                            duration: 0 // Disable transitions on hover
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Win Percentage Timeline',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        display: true,
                        position: 'right', // Move legend to the right for better visibility
                        labels: {
                            boxWidth: 12,
                            usePointStyle: true,
                            pointStyle: 'line',
                            filter: function (legendItem, chartData) {
                                // Don't show legend items for hidden datasets
                                return !legendItem.text.startsWith('_hidden_');
                            }
                        },
                        onClick: function (e, legendItem, legend) {
                            // Get the index in the datasets array
                            const index = legend.chart.data.datasets.findIndex(
                                d => d.label === legendItem.text
                            );
                            if (index >= 0) {
                                // Use a direct approach for highlighting a line
                                highlightLineByIndex(index);
                            }
                        }
                    },
                    tooltip: {
                        enabled: false // Completely disable tooltips
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Timeline Index'
                        },
                        reverse: false // Display normally, index 0 on left increasing to the right
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Win Probability (%)'
                        },
                        beginAtZero: true, // Always start at 0
                        suggestedMax: 50, // Default upper bound around 50%
                        ticks: {
                            callback: function (value) {
                                return value + '%';
                            }
                        }
                    }
                },
                hover: {
                    mode: 'nearest',
                    intersect: false
                }
            }
        });

        // Direct function to highlight a specific line by index
        function highlightLineByIndex(datasetIndex) {
            if (!winChart) return;

            const datasets = winChart.data.datasets;
            // Filter out hidden datasets
            const userDatasets = datasets.filter(d => !d.label.startsWith('_hidden_'));

            if (datasetIndex < 0 || datasetIndex >= userDatasets.length) return;

            const targetDataset = userDatasets[datasetIndex];
            const isAlreadyHighlighted = targetDataset.borderWidth > 2;

            // Reset all lines first
            userDatasets.forEach(dataset => {
                // If we're turning off highlight, restore all to normal
                if (isAlreadyHighlighted) {
                    dataset.borderWidth = 1.5;
                    dataset.borderColor = dataset.originalColor;
                    dataset.backgroundColor = dataset.originalColor;
                    dataset.z = 0;
                    dataset.pointRadius = 0;
                    dataset.pointHoverRadius = 4;
                } else {
                    // Otherwise dim all lines except the target
                    dataset.borderWidth = 1;
                    dataset.z = 0;
                    dataset.pointRadius = 0;
                    dataset.pointHoverRadius = 3;
                    // Make all lines semi-transparent except the one we're highlighting
                    if (dataset !== targetDataset) {
                        dataset.borderColor = dataset.originalColor.replace('1)', '0.15)');
                    }
                }
            });

            // Highlight the selected line (unless turning off)
            if (!isAlreadyHighlighted) {
                targetDataset.borderWidth = 3;
                targetDataset.borderColor = targetDataset.originalColor;
                targetDataset.backgroundColor = targetDataset.originalColor;
                targetDataset.pointRadius = 3;
                targetDataset.pointHoverRadius = 5;
                targetDataset.z = 10;
            }

            winChart.update();
        }

        // Add click handler to the chart to focus on a user
        ctx.onclick = function (evt) {
            const points = winChart.getElementsAtEventForMode(evt, 'nearest', { intersect: false }, true);

            if (points.length) {
                const datasetIndex = points[0].datasetIndex;
                // Only toggle focus if it's not a hidden dataset
                if (!winChart.data.datasets[datasetIndex].label.startsWith('_hidden_')) {
                    // Get the index among visible datasets
                    const visibleDatasets = winChart.data.datasets.filter(d => !d.label.startsWith('_hidden_'));
                    const visibleIndex = visibleDatasets.indexOf(winChart.data.datasets[datasetIndex]);
                    if (visibleIndex >= 0) {
                        highlightLineByIndex(visibleIndex);
                    }
                }
            }
        };
    }

    // Old toggle function will be replaced by the new highlightLineByIndex function
    function toggleUserFocus(datasetIndex) {
        // Find the chart element and call our new function
        const datasets = winChart.data.datasets;
        const visibleDatasets = datasets.filter(d => !d.label.startsWith('_hidden_'));

        // If datasetIndex refers to the actual dataset array index, find the visible index
        if (datasetIndex < datasets.length) {
            const dataset = datasets[datasetIndex];
            const visibleIndex = visibleDatasets.indexOf(dataset);
            if (visibleIndex >= 0) {
                highlightLineByIndex(visibleIndex);
                return;
            }
        }

        // Otherwise assume it's already a visible index
        highlightLineByIndex(datasetIndex);
    }

    // Update the chart with data for a specific timeline index
    function updateChart(timelineIndex) {
        if (!winChart) return;

        // Store the data index
        currentTimelineIndex = timelineIndex;

        // If we don't have data yet, try to initialize with current users data
        if (allTimelineData.length === 0 && window.initialUsersData) {
            const initialData = {
                index: timelineIndex,
                users: window.initialUsersData
                    .filter(user => user.username !== 'PERFECT' && user.monte_carlo_pct_first_place !== undefined)
                    .map(user => ({
                        username: user.username,
                        win_probability: user.monte_carlo_pct_first_place || 0
                    }))
            };
            allTimelineData.push(initialData);

            // Log that we're initializing with initial data
            console.log(`Initializing chart with initial data at index ${timelineIndex}`);
        }

        // Check if we have data for this index
        const timelineData = allTimelineData.find(data => data.index === timelineIndex);
        if (!timelineData) {
            console.warn(`No win percentage data available for timeline index ${timelineIndex}`);
            return;
        }

        // Get max index we have data for
        const maxIndex = Math.max(...allTimelineData.map(data => data.index));

        // Set up chart labels - use all indices from 0 to max
        const labels = Array.from({ length: maxIndex + 1 }, (_, i) => i);

        // Get unique usernames across all timeline data
        const allUsernames = [...new Set(
            allTimelineData.flatMap(data =>
                data.users.map(user => user.username)
            )
        )].filter(username => username !== 'PERFECT');

        // Filter out usernames without any win probability data (to avoid empty lines)
        const validUsernames = allUsernames.filter(username => {
            for (const data of allTimelineData) {
                const userData = data.users.find(user => user.username === username);
                if (userData && userData.win_probability > 0) {
                    return true;
                }
            }
            return false;
        });

        // Create datasets for each user
        const datasets = validUsernames.map((username, i) => {
            // Get color index, cycling through available colors
            const colorIndex = i % colors.length;
            const color = colors[colorIndex];

            // Create data points for this user across all timeline indices
            // We need to reverse the data points to match the x-axis
            const data = labels.map(index => {
                // Reverse the index mapping to get data in correct order
                const reverseIndex = maxIndex - index;
                const timelineDataForIndex = allTimelineData.find(data => data.index === reverseIndex);
                if (!timelineDataForIndex) return null;

                const userData = timelineDataForIndex.users.find(user => user.username === username);
                return userData ? userData.win_probability : null;
            });

            return {
                label: username,
                data: data,
                borderColor: color,
                backgroundColor: color,
                originalColor: color,
                borderWidth: 1.5,
                pointRadius: 0,
                pointHoverRadius: 4,
                tension: 0.1,
                z: 0,
                fill: false,
                hoverBorderWidth: 3,
                hoverBorderColor: color
            };
        });

        // Remember which dataset was previously highlighted, if any
        let highlightedDataset = null;
        if (winChart.data.datasets && winChart.data.datasets.length > 0) {
            const userDatasets = winChart.data.datasets.filter(d => !d.label.startsWith('_hidden_'));
            highlightedDataset = userDatasets.find(d => d.borderWidth > 2);
        }

        // Update chart data - start fresh 
        winChart.data.labels = labels;
        winChart.data.datasets = datasets;

        // Add a simple vertical line marker for the current index
        if (currentTimelineIndex >= 0 && currentTimelineIndex < labels.length) {
            // Now currentTimelineIndex is already the data index, not the slider position
            // The marker should be positioned at the correct x-axis position in the chart
            // Since our chart x-axis is reversed compared to the data index (0 = left, max = right),
            // we need to convert the data index to the chart position
            const markerIndex = maxIndex - currentTimelineIndex;

            // Log marker positioning for debugging
            console.log(`Marker positioning - data index: ${currentTimelineIndex}, maxIndex: ${maxIndex}, chart position: ${markerIndex}`);

            // Only use the point marker for cleaner visualization
            winChart.data.datasets.push({
                label: '_hidden_point_',
                data: labels.map((_, i) => i === markerIndex ? 50 : null), // Place in middle of y-axis
                borderColor: 'rgba(0, 0, 0, 0)',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                pointRadius: 6,
                pointHoverRadius: 6,
                pointStyle: 'circle',
                tension: 0,
                z: 10
            });
        }

        // Dynamically set the y-axis max based on the data with tighter constraints
        const allValues = datasets.flatMap(d => d.data.filter(v => v !== null));
        if (allValues.length > 0) {
            const maxValue = Math.max(...allValues);
            // Upper bound: either 50% or 5% more than max value, whichever is smaller
            const yMax = Math.min(50, Math.ceil((maxValue * 1.05) / 5) * 5);
            winChart.options.scales.y.max = Math.max(yMax, 10); // At least 10% for visibility
        } else {
            winChart.options.scales.y.max = 50; // Default cap at 50%
        }

        // If we had a highlighted dataset before, restore the highlight
        if (highlightedDataset) {
            const matchingNewDataset = datasets.find(d => d.label === highlightedDataset.label);
            if (matchingNewDataset) {
                const index = datasets.indexOf(matchingNewDataset);
                if (index >= 0) {
                    setTimeout(() => {
                        highlightLineByIndex(index);
                    }, 10);
                }
            }
        }

        winChart.update();
    }

    // Fetch win percentage data for a specific timeline index
    function fetchWinPercentageData(timelineIndex) {
        // Check if we already have this data
        if (allTimelineData.some(data => data.index === timelineIndex)) {
            updateChart(timelineIndex);
            return;
        }

        // Otherwise fetch it
        fetch(`/api/user-scores?truth_index=${timelineIndex}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.users) {
                    console.error('Invalid data structure received:', data);
                    return;
                }

                // Store the data for this timeline index
                allTimelineData.push({
                    index: timelineIndex,
                    users: data.users.map(user => ({
                        username: user.username,
                        win_probability: user.monte_carlo_pct_first_place || 0
                    }))
                });

                // Update chart with new data
                updateChart(timelineIndex);
            })
            .catch(error => {
                console.error('Error fetching win percentage data:', error);
            });
    }

    // Load all timeline data up to a specific index
    function loadAllTimelineData(currentIndex) {
        // This function expects currentIndex to be a data index (0 = newest, maxValue = oldest)
        // NOT the slider position. The slider position is inverted (0 = oldest, maxValue = newest)
        console.log(`Loading timeline data for data index: ${currentIndex}`);

        // If we already have all the data loaded, just update the chart
        if (allTimelineData.length > 0) {
            updateChart(currentIndex);
            return;
        }

        // Show loading indicator if available
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('visible');
        }

        // Use the new batch API endpoint to get all timeline data at once
        fetch('/api/user-scores-all-truth')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (!data || !data.timeline_data) {
                    console.error('Invalid data structure received from batch API:', data);
                    return;
                }

                // Process and store all timeline data at once
                allTimelineData = data.timeline_data;
                console.log(`Loaded data for all ${allTimelineData.length} timeline points`);

                // Update chart with the current index
                updateChart(currentIndex);

                // Hide loading indicator if available
                if (loadingOverlay) {
                    loadingOverlay.classList.remove('visible');
                }
            })
            .catch(error => {
                console.error('Error fetching batch timeline data:', error);

                // Hide loading indicator if available
                if (loadingOverlay) {
                    loadingOverlay.classList.remove('visible');
                }

                // Fall back to the old method if the batch API fails
                fallbackToIndividualLoading(currentIndex);
            });
    }

    // Fallback method using the original individual requests approach
    function fallbackToIndividualLoading(currentIndex) {
        console.log("Falling back to individual timeline loading");

        // Get the maximum index (oldest data)
        const slider = document.getElementById('truth-file-slider');
        if (!slider) return;

        const maxIndex = parseInt(slider.max);

        // Find which indices we need to load - LOAD ALL INDICES, not just up to current
        const indicesToLoad = [];
        for (let i = 0; i <= maxIndex; i++) {
            if (!allTimelineData.some(data => data.index === i)) {
                indicesToLoad.push(i);
            }
        }

        // If no indices to load, just update the chart
        if (indicesToLoad.length === 0) {
            updateChart(currentIndex);
            return;
        }

        // Show loading indicator if available
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('visible');
        }

        // Use Promise.all to load all missing indices in parallel
        const fetchPromises = indicesToLoad.map(index =>
            fetch(`/api/user-scores?truth_index=${index}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (!data || !data.users) {
                        console.error(`Invalid data structure received for index ${index}:`, data);
                        return null;
                    }

                    return {
                        index: index,
                        data: data
                    };
                })
                .catch(error => {
                    console.error(`Error fetching data for index ${index}:`, error);
                    return null;
                })
        );

        Promise.all(fetchPromises)
            .then(results => {
                // Filter out null results and process the data
                results.filter(result => result !== null).forEach(result => {
                    allTimelineData.push({
                        index: result.index,
                        users: result.data.users.map(user => ({
                            username: user.username,
                            win_probability: user.monte_carlo_pct_first_place || 0
                        }))
                    });
                });

                // Update chart with the current index
                updateChart(currentIndex);

                // Hide loading indicator if available
                if (loadingOverlay) {
                    loadingOverlay.classList.remove('visible');
                }
            });
    }

    // Initialize chart when DOM is loaded
    initializeChart();

    // Handle the case where we need to add our handler to the existing timeline slider
    function setupTimelineEventHandler() {
        // Try to find the timeline slider function
        if (window.fetchAndUpdateData) {
            // Store original function reference
            const originalFetchAndUpdateData = window.fetchAndUpdateData;

            // Override it with our version that also updates the chart
            window.fetchAndUpdateData = function (index) {
                // This function now consistently receives 'index' as a data index
                // (NOT a slider position) where:
                // - index 0 = newest game (tournament start)
                // - maxValue = oldest game (tournament end)
                console.log(`Chart: fetchAndUpdateData called with data index: ${index}`);

                // Call the original function which now consistently expects data index
                originalFetchAndUpdateData(index);

                // Get maximum index value
                const slider = document.getElementById('truth-file-slider');
                const maxValue = slider ? parseInt(slider.max) : 0;

                // Store the data index directly
                currentTimelineIndex = index;

                // Load timeline data - since we're now consistently working with data indices,
                // we can pass it directly without conversion
                loadAllTimelineData(index);
            };

            // Initialize with current data
            const slider = document.getElementById('truth-file-slider');
            if (slider) {
                const currentSliderValue = parseInt(slider.value);
                const maxValue = parseInt(slider.max);

                // Convert slider value to data index
                const dataIndex = maxValue - currentSliderValue;

                // Log debug info about indices
                console.log(`Chart init - Slider value: ${currentSliderValue}, Max: ${maxValue}, Data index: ${dataIndex}`);

                // Call the update function with the data index
                window.fetchAndUpdateData(dataIndex);
            }
        } else {
            // If the function doesn't exist yet, try again shortly
            setTimeout(setupTimelineEventHandler, 100);
        }
    }

    // Start the setup process
    setupTimelineEventHandler();
}); 