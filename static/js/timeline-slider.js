/**
 * Timeline Slider - Shared functionality for the tournament timeline
 * Used across the bracket page and users list page
 */
document.addEventListener('DOMContentLoaded', function () {
    // Get DOM elements
    const truthSlider = document.getElementById('truth-file-slider');
    const currentTruthFile = document.getElementById('current-truth-file');
    const prevButton = document.getElementById('prev-truth-file');
    const nextButton = document.getElementById('next-truth-file');
    const jumpStartButton = document.getElementById('jump-start');
    const jumpEndButton = document.getElementById('jump-end');

    if (truthSlider && currentTruthFile) {
        // Get the max slider value
        const maxSliderValue = parseInt(truthSlider.max);

        // Update button states based on current position
        function updateButtonStates(sliderValue) {
            prevButton.disabled = sliderValue <= 0;
            nextButton.disabled = sliderValue >= maxSliderValue;
        }

        // Consistently convert between slider value and index
        // Our model: Slider shows oldest (highest index) on left, newest (index 0) on right
        // This means slider value 0 = oldest file (highest index), and maxSliderValue = newest file (index 0)
        function sliderValueToIndex(value) {
            return maxSliderValue - parseInt(value);
        }

        // Initialize button states
        updateButtonStates(parseInt(truthSlider.value));

        // Track the timer for debouncing slider movement
        let sliderTimer;

        // Add event listeners for the slider
        truthSlider.addEventListener('input', function () {
            // Update displayed filename immediately
            const fileNames = JSON.parse(document.getElementById('timeline-data').dataset.filenames);
            const sliderValue = parseInt(this.value);
            const index = sliderValueToIndex(sliderValue);

            if (fileNames && index >= 0 && index < fileNames.length) {
                currentTruthFile.textContent = fileNames[index];
            }

            // Update button states
            updateButtonStates(sliderValue);

            // Clear existing timer
            clearTimeout(sliderTimer);

            // Set a timer to update data with slight delay for performance
            sliderTimer = setTimeout(function () {
                // Call the appropriate update function based on which page we're on
                if (typeof fetchBracketData === 'function') {
                    fetchBracketData(index);
                } else if (typeof fetchAndUpdateData === 'function') {
                    fetchAndUpdateData(index);
                } else {
                    console.warn('No update function found for timeline slider');
                }
            }, 10);
        });

        // Add handlers for previous and next buttons
        prevButton.addEventListener('click', function () {
            let currentValue = parseInt(truthSlider.value);
            if (currentValue > 0) {
                truthSlider.value = currentValue - 1;
                truthSlider.dispatchEvent(new Event('input'));
            }
        });

        nextButton.addEventListener('click', function () {
            let currentValue = parseInt(truthSlider.value);
            if (currentValue < maxSliderValue) {
                truthSlider.value = currentValue + 1;
                truthSlider.dispatchEvent(new Event('input'));
            }
        });

        // Add handlers for jump-start and jump-end buttons
        jumpStartButton.addEventListener('click', function () {
            truthSlider.value = 0; // Set to beginning (oldest files on left)
            truthSlider.dispatchEvent(new Event('input'));
        });

        jumpEndButton.addEventListener('click', function () {
            truthSlider.value = maxSliderValue; // Set to end (newest files on right)
            truthSlider.dispatchEvent(new Event('input'));
        });
    }
}); 