document.addEventListener('DOMContentLoaded', () => {
    // Array of loading phrases
    const loadingPhrases = [
        "fetching the vibes... almost there!",
        "spinning up the creativity engine...",
        "your playlist just got curious about your style.",
        "magic takes a moment... hold tight!",
        "building a soundtrack to your soul.",
        "scanning your music DNA... decoding awesome.",
        "just a beat away from brilliance.",
        "pulling top picks from the universe...",
        "loading your musical aura... stand by.",
        "syncing with the music gods... one sec!",
        "turning your top tracks into masterpieces.",
        "visualizing your musical universe...",
        "piecing together your perfect recommendations."
    ];

    // Function to get a random index
    function getRandomIndex(max) {
        return Math.floor(Math.random() * max);
    }

    // Function to create and show the loading spinner
    function showLoadingSpinner() {
        // Create spinner container
        const spinnerContainer = document.createElement('div');
        spinnerContainer.id = 'loading-spinner';
        spinnerContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;

        // Create spinner element
        const spinner = document.createElement('div');
        spinner.style.cssText = `
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #4379FF;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        `;

        // Create loading text element
        const loadingText = document.createElement('div');
        loadingText.id = 'loading-text';
        loadingText.style.cssText = `
            font-size: 1rem;
            color: #4379FF;
            text-align: center;
            max-width: 300px;
            height: 30px;
            opacity: 1;
            transition: opacity 0.5s ease-in-out;
        `;

        // Add style for animations
        const styleSheet = document.createElement('style');
        styleSheet.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            @keyframes fadeOut {
                0% { opacity: 1; }
                100% { opacity: 0; }
            }
            @keyframes fadeIn {
                0% { opacity: 0; }
                100% { opacity: 1; }
            }
        `;
        document.head.appendChild(styleSheet);

        // Append spinner and text to container
        spinnerContainer.appendChild(spinner);
        spinnerContainer.appendChild(loadingText);
        document.body.appendChild(spinnerContainer);

        // Start with a random phrase
        let currentPhraseIndex = getRandomIndex(loadingPhrases.length);
        
        function cycleLoadingText() {
            // Fade out the current text
            loadingText.style.animation = 'fadeOut 0.5s ease-in-out forwards';
            
            // Wait for fade-out to complete, then change text and fade in
            setTimeout(() => {
                // Move to next phrase
                currentPhraseIndex = (currentPhraseIndex + 1) % loadingPhrases.length;
                loadingText.textContent = loadingPhrases[currentPhraseIndex];
                
                // Fade in the new text
                loadingText.style.animation = 'fadeIn 0.5s ease-in-out forwards';
            }, 500); // matches the fade-out animation duration
        }

        // Initial text
        loadingText.textContent = loadingPhrases[currentPhraseIndex];
        
        // Change phrase every 2 seconds
        const phraseInterval = setInterval(cycleLoadingText, 2000);

        return { 
            spinnerContainer, 
            stopCarousel: () => clearInterval(phraseInterval) 
        };
    }

    // Function to remove the loading spinner
    function removeLoadingSpinner() {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            // Stop the phrase carousel before removing
            const stopCarousel = spinner.dataset.stopCarousel;
            if (stopCarousel) {
                stopCarousel();
            }
            spinner.remove();
        }
    }

    // Add event listeners to buttons that trigger long-running processes
    const imageGenerationBtn = document.querySelector('a[href*="display-image"] button');
    const recommendedSongsBtn = document.querySelector('a[href*="display-recommended-songs"] button');

    if (imageGenerationBtn) {
        imageGenerationBtn.addEventListener('click', (e) => {
            const { spinnerContainer, stopCarousel } = showLoadingSpinner();
            spinnerContainer.dataset.stopCarousel = stopCarousel;
        });
    }

    if (recommendedSongsBtn) {
        recommendedSongsBtn.addEventListener('click', (e) => {
            const { spinnerContainer, stopCarousel } = showLoadingSpinner();
            spinnerContainer.dataset.stopCarousel = stopCarousel;
        });
    }

    // Remove spinner when page content is fully loaded
    window.addEventListener('load', removeLoadingSpinner);

    // Fallback to remove spinner if it's still present after a timeout
    setTimeout(removeLoadingSpinner, 30000); // 30 seconds timeout
});