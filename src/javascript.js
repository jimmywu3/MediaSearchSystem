document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('add-movie-modal');
    const openBtn = document.getElementById('open-add-modal');
    const closeBtn = document.getElementById('close-modal-btn');
    const form = document.getElementById('add-movie-form');
    const searchInput = document.getElementById('movie-search');
    const datalist = document.getElementById('movie-suggestions');
    const ratingInput = document.getElementById('rating');
    const ratingDisplay = document.getElementById('rating-value');
    const openProfileBtn = document.getElementById('open-profile');
    const profileModal = document.getElementById('profile-modal');
    const closeProfileBtn = document.getElementById('close-profile-modal');
    const historyBody = document.getElementById('history-body');

    // Debug modal elements
    const debugModal = document.getElementById('debug-modal');
    const openDebugBtn = document.getElementById('open-debug');
    const closeDebugBtn = document.getElementById('close-debug-modal');
    const debugHourInput = document.getElementById('debug-hour');
    const debugSetBtn = document.getElementById('debug-set-btn');
    const debugClearBtn = document.getElementById('debug-clear-btn');

    // 1. Modal Toggle Logic
    openBtn.addEventListener('click', (e) => {
        e.preventDefault();
        modal.showModal();
    });

    closeBtn.addEventListener('click', () => {
        modal.close();
        form.reset();
    });

    // Profile modal handlers
    if (openProfileBtn && profileModal) {
        openProfileBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            profileModal.showModal();
            await loadWatchHistory();
        });
    }

    if (closeProfileBtn) {
        closeProfileBtn.addEventListener('click', () => {
            profileModal.close();
            if (historyBody)
                historyBody.innerHTML =
                    '<tr><td colspan="3">Loading…</td></tr>';
        });
    }

    // Debug Modal Logic
    if (openDebugBtn && debugModal) {
        openDebugBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const overriddenHour = localStorage.getItem('debugHourOverride');
            if (overriddenHour !== null) {
                debugHourInput.value = overriddenHour;
            }
            debugModal.showModal();
        });
    }

    if (closeDebugBtn) {
        closeDebugBtn.addEventListener('click', () => {
            debugModal.close();
        });
    }

    if (debugSetBtn) {
        debugSetBtn.addEventListener('click', () => {
            const hour = parseInt(debugHourInput.value, 10);
            if (Number.isFinite(hour) && hour >= 0 && hour <= 23) {
                localStorage.setItem('debugHourOverride', hour);
                console.log(`Debug: Hour override set to ${hour}`);
                debugModal.close();
                // Refresh all rows to see the new hour-based data
                fetchAndRender('cards1', 3, '/api/recommended/scoring');
                fetchAndRender('cards2', 3, '/api/recommended/genre');
                fetchAndRender('cards3', 3, '/api/recommended');
            } else {
                alert('Please enter a valid hour (0-23)');
            }
        });
    }

    if (debugClearBtn) {
        debugClearBtn.addEventListener('click', () => {
            localStorage.removeItem('debugHourOverride');
            console.log('Debug: Hour override cleared');
            debugModal.close();
            // Refresh all rows to see the actual current hour data
            fetchAndRender('cards1', 3, '/api/recommended/scoring');
            fetchAndRender('cards2', 3, '/api/recommended/genre');
            fetchAndRender('cards3', 3, '/api/recommended');
        });
    }

    // 2. Form Submission Logic
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const movieTitle = formData.get('movie-search');
        const userRating = Number(parseFloat(formData.get('rating')));
        const watchedHour = Number(formData.get('watched-hour'));
        const watchedTime = Number.isFinite(watchedHour)
            ? `${String(watchedHour).padStart(2, '0')}:00:00`
            : '';

        const normalizedTitle = (movieTitle || '').trim().toLowerCase();
        const match = lastSuggestions.find(
            (m) => m.title.toLowerCase() === normalizedTitle,
        );
        const payload = {
            rating: userRating,
            time_watched: watchedTime,
        };

        if (match) {
            payload.title_id = match.title_id;
        } else {
            payload.title = movieTitle;
        }

        console.log(
            `Movie: ${movieTitle}, Rating: ${userRating}, Watched at: ${watchedTime}`,
        );

        try {
            const res = await fetch('/api/rate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => null);
                throw new Error(err?.error || 'Failed to save rating');
            }

            console.log('Rating saved successfully');
        } catch (err) {
            console.error(err);
            alert('Unable to save rating at this time.');
        }

        modal.close();
        form.reset();
    });

    // 3. Auto-complete Logic (real DB search)
    const MIN_SEARCH_LENGTH = 2;
    let searchDebounce;
    let lastSuggestions = [];

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        datalist.innerHTML = '';

        if (query.length < MIN_SEARCH_LENGTH) return;

        // Debounce to reduce request volume while typing
        if (searchDebounce) clearTimeout(searchDebounce);
        searchDebounce = setTimeout(async () => {
            try {
                const res = await fetch(
                    `/api/search?q=${encodeURIComponent(query)}`,
                );
                if (!res.ok) throw new Error('Network response was not ok');
                const movies = await res.json();

                lastSuggestions = movies;
                movies.forEach((m) => {
                    const option = document.createElement('option');
                    option.value = m.title;
                    datalist.appendChild(option);
                });
            } catch (err) {
                console.error('Failed to fetch movie suggestions', err);
            }
        }, 250);
    });

    if (ratingInput && ratingDisplay) {
        ratingDisplay.textContent = ratingInput.value;
        ratingInput.addEventListener('input', () => {
            ratingDisplay.textContent = ratingInput.value;
        });
    }

    async function loadWatchHistory() {
        if (!historyBody) return;

        try {
            const res = await fetch('/api/history');
            if (!res.ok) throw new Error('Failed to load history');
            const history = await res.json();

            if (!Array.isArray(history) || history.length === 0) {
                historyBody.innerHTML =
                    '<tr><td colspan="3">No watch history yet.</td></tr>';
                return;
            }

            historyBody.innerHTML = '';
            history.forEach((row) => {
                const tr = document.createElement('tr');
                const rating = row.rating != null ? Number(row.rating) : null;
                tr.innerHTML = `
                    <td>${escapeHtml(row.title)}</td>
                    <td>${rating != null && !Number.isNaN(rating) ? rating.toFixed(1) : '—'}</td>
                    <td>${row.watched_at || '—'}</td>
                `;
                historyBody.appendChild(tr);
            });
        } catch (err) {
            console.error(err);
            historyBody.innerHTML =
                '<tr><td colspan="3">Unable to load history.</td></tr>';
        }
    }

    async function fetchAndRender(
        targetSelector,
        limit = 3,
        endpoint = '/api/recommended',
    ) {
        try {
            // Add debug hour override if set
            const debugHour = localStorage.getItem('debugHourOverride');
            const url = debugHour
                ? `${endpoint}?debug_hour=${debugHour}`
                : endpoint;

            const res = await fetch(url);
            if (!res.ok) throw new Error('Network response was not ok');
            const data = await res.json();

            // Handle genre endpoint which returns { movies, genre_name, movie_name }
            let movies = Array.isArray(data) ? data : data.movies || [];

            // Update Row 2 title if this is the genre endpoint
            if (endpoint === '/api/recommended/genre' && data.genre_name) {
                const titleEl = document.getElementById('row2-title');
                if (titleEl) {
                    titleEl.textContent = `Because you like "${escapeHtml(data.genre_name)}" (from "${escapeHtml(data.movie_name)}")`;
                }
            }

            // Update Row 3 title if this is the recommended endpoint
            if (endpoint === '/api/recommended' && data.genre_names) {
                const titleEl = document.getElementById('row3-title');
                if (titleEl) {
                    const hour = data.current_hour;
                    titleEl.textContent = `Recommended for ${hour}:00 - ${escapeHtml(data.genre_names)}`;
                }
            }

            const container = document.querySelector(`.${targetSelector}`);
            if (!container) return;
            container.innerHTML = '';

            // show only up to `limit` cards
            movies.slice(0, limit).forEach((m) => {
                const card = document.createElement('div');
                card.className = 'skeleton-card';

                // Build poster image HTML if poster_path exists
                const posterHtml = m.poster_path
                    ? `<img src="https://image.tmdb.org/t/p/w185${m.poster_path}" alt="${escapeHtml(m.title)}" class="poster-image" />`
                    : `<div class="poster-placeholder"></div>`;

                card.innerHTML = `
                    ${posterHtml}
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

    fetchAndRender('cards1', 3, '/api/recommended/scoring');
    fetchAndRender('cards2', 3, '/api/recommended/genre');
    fetchAndRender('cards3', 3, '/api/recommended');

    document.querySelectorAll('.refresh-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            const target = btn.getAttribute('data-target');
            if (!target) return;

            // Determine endpoint based on target
            let endpoint = '/api/recommended';
            if (target === 'cards1') endpoint = '/api/recommended/scoring';
            else if (target === 'cards2') endpoint = '/api/recommended/genre';

            fetchAndRender(target, 3, endpoint);
        });
    });
});
