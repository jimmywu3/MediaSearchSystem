document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('add-movie-modal');
    const openBtn = document.getElementById('open-add-modal');
    const closeBtn = document.getElementById('close-modal-btn');
    const form = document.getElementById('add-movie-form');
    const searchInput = document.getElementById('movie-search');
    const datalist = document.getElementById('movie-suggestions');

    // 1. Modal Toggle Logic
    openBtn.addEventListener('click', (e) => {
        e.preventDefault(); // Prevents the anchor tag from reloading the page
        modal.showModal();
    });

    closeBtn.addEventListener('click', () => {
        modal.close();
        form.reset(); // Clears the form when closed
    });

    // 2. Form Submission Logic
    form.addEventListener('submit', (e) => {
        e.preventDefault(); // Prevents the page from reloading on submit

        // Extract data
        const formData = new FormData(form);
        const movieTitle = formData.get('movie-search');
        const userRating = formData.get('rating');

        console.log(`Movie: ${movieTitle}, Rating: ${userRating}`);
        
        // Here you would eventually write logic to add the movie to your UI
        
        modal.close();
        form.reset();
    });

    // 3. Mock Auto-complete Logic
    // In a real application, you replace this static array with a fetch() call to a movie API
    const mockDatabase = [
        "Inception", "Interstellar", "Iron Man", 
        "The Matrix", "The Lord of the Rings", "The Dark Knight",
        "Avatar", "Avengers: Endgame", "Alien"
    ];

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        
        // Clear previous suggestions
        datalist.innerHTML = '';

        if (query.length < 2) return; // Wait until 2 characters are typed

        // Filter mock database (This simulates an API search)
        const matches = mockDatabase.filter(movie => movie.toLowerCase().includes(query));

        // Populate the <datalist>
        matches.forEach(match => {
            const option = document.createElement('option');
            option.value = match;
            datalist.appendChild(option);
        });
    });
});