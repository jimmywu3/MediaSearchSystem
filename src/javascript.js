document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('add-movie-modal');
    const openBtn = document.getElementById('open-add-modal');
    const closeBtn = document.getElementById('close-modal-btn');
    const form = document.getElementById('add-movie-form');
    const searchInput = document.getElementById('movie-search');
    const datalist = document.getElementById('movie-suggestions');
    const ratingInput = document.getElementById('rating');
    const ratingDisplay = document.getElementById('rating-value');

    // 1. Modal Toggle Logic
    openBtn.addEventListener('click', (e) => {
        e.preventDefault(); 
        modal.showModal();
    });

    closeBtn.addEventListener('click', () => {
        modal.close();
        form.reset(); 
    });

    // 2. Form Submission Logic
    form.addEventListener('submit', (e) => {
        e.preventDefault(); 

        const formData = new FormData(form);
        const movieTitle = formData.get('movie-search');

        const userRating = Number(parseFloat(formData.get('rating')));

        console.log(`Movie: ${movieTitle}, Rating: ${userRating}`);

        // TODO: Still needa add stuff to push to our database for the user

        modal.close();
        form.reset();
    });

    // 3. Mock Auto-complete Logic will turn this into something usable and reflects our database later
    const mockDatabase = [
        'Inception',
        'Interstellar',
        'Iron Man',
        'The Matrix',
        'The Lord of the Rings',
        'The Dark Knight',
        'Avatar',
        'Avengers: Endgame',
        'Alien',
    ];

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();

        datalist.innerHTML = '';

        if (query.length < 2) return; 

        const matches = mockDatabase.filter((movie) =>
            movie.toLowerCase().includes(query),
        );

        matches.forEach((match) => {
            const option = document.createElement('option');
            option.value = match;
            datalist.appendChild(option);
        });
    });

    if (ratingInput && ratingDisplay) {
        ratingDisplay.textContent = ratingInput.value;
        ratingInput.addEventListener('input', () => {
            ratingDisplay.textContent = ratingInput.value;
        });
    }

    async function fetchAndRender(targetSelector, limit = 3) {
        try {
            const res = await fetch('/api/recommended');
            if (!res.ok) throw new Error('Network response was not ok');
            const movies = await res.json();
            const container = document.querySelector(`.${targetSelector}`);
            if (!container) return;
            container.innerHTML = '';

            // show only up to `limit` cards
            movies.slice(0, limit).forEach((m) => {
                const card = document.createElement('div');
                card.className = 'skeleton-card';
                card.innerHTML = `
                    <div class="poster-placeholder"></div>
                    <div class="movie-title">${escapeHtml(m.title)} (${m.release_year || 'N/A'})</div>
                    <div class="movie-sub">Rating: ${m.avg_rating || 'N/A'}</div>
                `;
                container.appendChild(card);
            });
        } catch (err) {
            console.error(`Failed to fetch movies for ${targetSelector}`, err);
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>"']/g, function (s) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;',
            }[s];
        });
    }

    fetchAndRender('cards1', 3);
    fetchAndRender('cards2', 3);
    fetchAndRender('cards3', 3);

    document.querySelectorAll('.refresh-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            const target = btn.getAttribute('data-target');
            if (!target) return;
            fetchAndRender(target, 3);
        });
    });
});
