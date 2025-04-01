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
                        position: 'top',
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
                            // Find the index of the clicked dataset
                            const index = legend.chart.data.datasets.findIndex(
                                d => d.label === legendItem.text
                            );
                            if (index >= 0) {
                                toggleUserFocus(index);
                            }
                        }
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function (tooltipItems) {
                                // Get the truth file name from the timeline data
                                const fileNames = JSON.parse(document.getElementById('timeline-data').dataset.filenames || '[]');
                                const index = tooltipItems[0].parsed.x;
                                // Convert chart index to file index (reversed)
                                const maxIndex = fileNames.length - 1;
                                const fileIndex = maxIndex - index;

                                if (fileIndex >= 0 && fileIndex < fileNames.length) {
                                    return fileNames[fileIndex].replace('.json', '');
                                }
                                return `Timeline Index: ${index}`;
                            },
                            label: function (context) {
                                // Skip labels for hidden datasets
                                if (context.dataset.label.startsWith('_hidden_')) {
                                    return null;
                                }

                                if (context.raw === null) return context.dataset.label + ': N/A';
                                return context.dataset.label + ': ' +
                                    context.raw.toFixed(2) + '%';
                            }
                        }
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
                        reverse: true // Reverse x-axis so newest (index 0) is on the right
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Win Probability (%)'
                        },
                        beginAtZero: true, // Always start at 0
                        // We'll set max dynamically based on data
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

        // Add click handler to the chart to focus on a user
        ctx.onclick = function (evt) {
            const points = winChart.getElementsAtEventForMode(evt, 'nearest', { intersect: false }, true);

            if (points.length) {
                const datasetIndex = points[0].datasetIndex;
                // Only toggle focus if it's not a hidden dataset
                if (!winChart.data.datasets[datasetIndex].label.startsWith('_hidden_')) {
                    toggleUserFocus(datasetIndex);
                }
            }
        };
    }

    // Toggle focus on a specific user's line
    function toggleUserFocus(datasetIndex) {
        if (!winChart) return;

        const datasets = winChart.data.datasets;

        // Find the actual user dataset (filtering out the current position indicator)
        const userDatasets = datasets.filter(d => !d.label.startsWith('_hidden_'));

        // Make sure the index is valid for user datasets
        if (datasetIndex >= userDatasets.length) return;

        const focusedDataset = userDatasets[datasetIndex];

        // Check if we're already focusing on this dataset
        const isAlreadyFocused = focusedDataset.borderWidth === 3;

        // Reset all user datasets to default appearance
        userDatasets.forEach(dataset => {
            dataset.borderWidth = 1.5;
            dataset.borderColor = dataset.originalColor;
            dataset.backgroundColor = dataset.originalColor;
            dataset.pointRadius = 0;
            dataset.pointHoverRadius = 3;
            dataset.z = 0;

            // Make lines semi-transparent
            if (!isAlreadyFocused || datasetIndex !== userDatasets.indexOf(dataset)) {
                dataset.borderColor = dataset.originalColor.replace('1)', '0.3)');
            }
        });

        // If not already focused, highlight the selected dataset
        if (!isAlreadyFocused) {
            focusedDataset.borderWidth = 3;
            focusedDataset.borderColor = focusedDataset.originalColor;
            focusedDataset.pointRadius = 2;
            focusedDataset.pointHoverRadius = 5;
            focusedDataset.z = 10;
        }

        winChart.update();
    }

    // Update the chart with data for a specific timeline index
    function updateChart(timelineIndex) {
        if (!winChart) return;

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
            const data = labels.map(index => {
                const timelineDataForIndex = allTimelineData.find(data => data.index === index);
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

        // Update chart data - start fresh 
        winChart.data.labels = labels;
        winChart.data.datasets = datasets;

        // Add a simple vertical line marker for the current index
        if (currentTimelineIndex >= 0 && currentTimelineIndex < labels.length) {
            // Add vertical line using a special dataset with sparse data
            const verticalLineData = Array(labels.length).fill(null);
            verticalLineData[currentTimelineIndex] = 100; // Only set a value at current index

            winChart.data.datasets.push({
                label: '_hidden_line_', // Hidden from legend
                data: verticalLineData,
                borderColor: 'rgba(0, 0, 0, 0.5)',
                borderWidth: 1.5,
                borderDash: [5, 3],
                pointRadius: 0,
                pointHoverRadius: 0,
                showLine: true,
                spanGaps: false, // Don't connect across null values
                fill: false,
                tension: 0,
                z: 5
            });

            // Add a single point marker dataset for the current index
            winChart.data.datasets.push({
                label: '_hidden_point_',
                data: labels.map((_, i) => i === currentTimelineIndex ? 50 : null), // Place in middle of y-axis
                borderColor: 'rgba(0, 0, 0, 0)',
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                pointRadius: 6,
                pointHoverRadius: 6,
                pointStyle: 'circle',
                tension: 0,
                z: 10
            });
        }

        // Dynamically set the y-axis max based on the data
        const allValues = datasets.flatMap(d => d.data.filter(v => v !== null));
        if (allValues.length > 0) {
            const maxValue = Math.max(...allValues);
            // Add 10% padding on top, rounded to nearest 5
            const yMax = Math.ceil((maxValue * 1.1) / 5) * 5;
            winChart.options.scales.y.max = Math.max(yMax, 10); // At least 10% for visibility
        } else {
            winChart.options.scales.y.max = 100; // Default if no data
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
        // Get the maximum index (oldest data)
        const slider = document.getElementById('truth-file-slider');
        if (!slider) return;

        const maxIndex = parseInt(slider.max);

        // Find which indices we need to load
        const indicesToLoad = [];
        for (let i = 0; i <= currentIndex; i++) {
            if (!allTimelineData.some(data => data.index === i)) {
                indicesToLoad.push(i);
            }
        }

        // If no indices to load, just update the chart
        if (indicesToLoad.length === 0) {
            updateChart(currentIndex);
            return;
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
                // Call the original function
                originalFetchAndUpdateData(index);

                // Load all timeline data up to this index and update our chart
                loadAllTimelineData(index);
            };

            // Initialize with current data
            const slider = document.getElementById('truth-file-slider');
            if (slider) {
                const currentIndex = parseInt(slider.value);
                const maxValue = parseInt(slider.max);
                const actualIndex = maxValue - currentIndex;
                loadAllTimelineData(actualIndex);
            }
        } else {
            // If the function doesn't exist yet, try again shortly
            setTimeout(setupTimelineEventHandler, 100);
        }
    }

    // Start the setup process
    setupTimelineEventHandler();
}); 