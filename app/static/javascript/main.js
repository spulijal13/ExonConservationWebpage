document.addEventListener('DOMContentLoaded', () => {
    const dataElement = document.getElementById('results-data');
    if (!dataElement) return;
    const initial = JSON.parse(dataElement.textContent);
    const container = document.getElementById('exon-results');
    const table = document.getElementById('results-table');
    const body = table.tBodies[0];
    const status = document.getElementById('results-status');
    const rowHeight = 32;
    const blockSize = 100;
    const cache = new Map([[0, initial.rows]]);
    let currentOffset = 0;
    let controller;
    let timer;
    table.style.width = `${initial.columns * 180}px`;

    function render(offset, rows) {
        const fragment = document.createDocumentFragment();
        function spacer(height) {
            if (height <= 0) return;
            const row = document.createElement('tr');
            row.className = 'results-spacer';
            row.setAttribute('aria-hidden', 'true');
            const cell = document.createElement('td');
            cell.colSpan = initial.columns;
            cell.style.height = `${height}px`;
            row.append(cell);
            fragment.append(row);
        }
        spacer(offset * rowHeight);
        for (const values of rows) {
            const row = document.createElement('tr');
            for (const value of values) {
                const cell = document.createElement('td');
                cell.textContent = value == null ? '' : String(value);
                cell.title = cell.textContent;
                row.append(cell);
            }
            fragment.append(row);
        }
        spacer(Math.max(0, initial.total - offset - rows.length) * rowHeight);
        body.replaceChildren(fragment);
    }

    async function update() {
        const index = Math.floor(container.scrollTop / rowHeight);
        const offset = Math.floor(index / blockSize) * blockSize;
        if (offset === currentOffset) return;
        currentOffset = offset;
        if (controller) controller.abort();
        if (cache.has(offset)) {
            render(offset, cache.get(offset));
            status.textContent = '';
            return;
        }
        // Preserve the full scroll range while the new window is fetched.
        render(offset, []);
        status.textContent = 'Loading rows…';
        controller = new AbortController();
        const url = new URL(window.location.href);
        url.searchParams.delete('download');
        url.searchParams.delete('file_format');
        url.searchParams.set('results_window', '1');
        url.searchParams.set('offset', String(offset));
        try {
            const response = await fetch(url, {signal: controller.signal});
            if (!response.ok) throw new Error('Could not load rows');
            const data = await response.json();
            if (currentOffset !== offset) return;
            cache.set(offset, data.rows);
            if (cache.size > 4) cache.delete(cache.keys().next().value);
            render(offset, data.rows);
            status.textContent = '';
        } catch (error) {
            if (error.name === 'AbortError' || currentOffset !== offset) return;
            currentOffset = -1;
            status.textContent = 'Could not load rows. Scroll to retry.';
        }
    }

    render(0, initial.rows);
    container.addEventListener('scroll', () => {
        clearTimeout(timer);
        timer = setTimeout(update, 60);
    }, {passive: true});
});
