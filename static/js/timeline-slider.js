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

        // CRITICAL FIX: Check if slider value looks like it might be inverted after page load
        // This prevents the oscillation between slider value and data index on refresh
        function checkAndFixInvertedSlider() {
            // Get current slider value
            const currentSliderValue = parseInt(truthSlider.value);

            // REVISED LOGIC: We need to be much more careful about when to "fix" a slider value
            // PROBLEM: When the slider value is high (like 52), it was being incorrectly identified
            // as a data index rather than a valid slider position

            console.log(`Timeline slider: Checking for inversion - Current: ${currentSliderValue}, Max: ${maxSliderValue}`);

            // Save the current URL parameters to see if truth_index is present
            const urlParams = new URLSearchParams(window.location.search);
            const urlTruthIndex = urlParams.get('truth_index');

            // Calculate what would be the "corrected" value if this was inverted
            const suspectedDataIndex = currentSliderValue;
            const correctedSliderValue = maxSliderValue - suspectedDataIndex;

            // Check if we have evidence that this is really inverted:
            // 1. The slider value must be very small compared to max (less than 10)
            // 2. We should NOT have a truth_index parameter in the URL (which indicates the value is already correct)
            const isLikelyInverted =
                currentSliderValue < 10 &&
                currentSliderValue < maxSliderValue / 6 && // Must be in the bottom 1/6th of the range
                urlTruthIndex === null && // No truth_index in URL
                correctedSliderValue > maxSliderValue / 2; // Corrected value would be in the top half

            console.log(`Timeline slider: Is likely inverted? ${isLikelyInverted} (current=${currentSliderValue}, corrected=${correctedSliderValue})`);

            if (isLikelyInverted) {
                console.log(`Timeline slider: Detected inverted index. Current: ${currentSliderValue}, Max: ${maxSliderValue}`);

                // Convert to correct slider position
                console.log(`Timeline slider: Correcting from ${currentSliderValue} to ${correctedSliderValue}`);

                // Update the slider UI
                truthSlider.value = correctedSliderValue;

                // Update displayed filename
                const fileNames = JSON.parse(document.getElementById('timeline-data').dataset.filenames);
                const index = suspectedDataIndex; // Use the data index directly

                if (fileNames && index >= 0 && index < fileNames.length) {
                    const displayName = fileNames[index].replace('.json', '');
                    currentTruthFile.textContent = displayName;
                }

                // Update button states
                updateButtonStates(correctedSliderValue);

                // Trigger the input event to update data
                truthSlider.dispatchEvent(new Event('input'));

                return true; // Indicate correction was made
            }

            return false; // No correction needed
        }

        // Run the check on page load
        setTimeout(checkAndFixInvertedSlider, 100);

        // Add event listeners for the slider
        truthSlider.addEventListener('input', function () {
            // Update displayed filename immediately
            const fileNames = JSON.parse(document.getElementById('timeline-data').dataset.filenames);
            const sliderValue = parseInt(this.value);
            const index = sliderValueToIndex(sliderValue);

            if (fileNames && index >= 0 && index < fileNames.length) {
                // Remove the .json extension before displaying
                const displayName = fileNames[index].replace('.json', '');
                currentTruthFile.textContent = displayName;
            }

            // Update button states
            updateButtonStates(sliderValue);

            // Clear existing timer
            clearTimeout(sliderTimer);

            // Set a timer to update data with slight delay for performance
            sliderTimer = setTimeout(function () {
                // CRITICAL FIX: Consistently pass the data index (not slider value) to update functions
                const dataIndex = sliderValueToIndex(sliderValue);
                console.log(`Timeline slider: Value=${sliderValue}, Data Index=${dataIndex}`);

                // Call the appropriate update function based on which page we're on
                if (typeof fetchBracketData === 'function') {
                    fetchBracketData(dataIndex);
                } else if (typeof fetchAndUpdateData === 'function') {
                    fetchAndUpdateData(dataIndex);
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