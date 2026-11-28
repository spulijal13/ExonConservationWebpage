document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('error-summary')?.focus();
    const dataElement = document.getElementById('results-data');
    if (!dataElement) return;
    const initial = JSON.parse(dataElement.textContent);
    const container = document.getElementById('exon-results');
    const table = document.getElementById('results-table');
    const body = table.tBodies[0];
    const status = document.getElementById('results-status');
    let rowHeight = body.rows[0].getBoundingClientRect().height;
    const retry = document.getElementById('retry-results');
    const jump = document.getElementById('result-jump');
    const blockSize = 100;
    const cache = new Map([[0, initial.rows]]);
    let currentOffset = 0;
    let controller;
    let timer;
    table.style.width = `${initial.columns * 14 + 4.5}rem`;

    function render(offset, rows) {
        const fragment = document.createDocumentFragment();
        function spacer(height) {
            if (height <= 0) return;
            const row = document.createElement('tr');
            row.className = 'results-spacer';
            row.setAttribute('aria-hidden', 'true');
            const cell = document.createElement('td');
            cell.colSpan = initial.columns + 1;
            cell.style.height = `${height}px`;
            row.append(cell);
            fragment.append(row);
        }
        spacer(offset * rowHeight);
        for (const [index, values] of rows.entries()) {
            const row = document.createElement('tr');
            row.setAttribute('aria-rowindex', String(offset + index + 2));
            const numberCell = document.createElement('td');
            numberCell.className = 'row-number';
            numberCell.textContent = String(offset + index + 1);
            row.append(numberCell);
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
        container.setAttribute('aria-busy', rows.length ? 'false' : 'true');
        retry.hidden = true;
        if (rows.length) status.textContent = `Rows ${offset + 1}–${offset + rows.length} of ${initial.total} loaded.`;
    }

    async function update() {
        const index = Math.floor(container.scrollTop / rowHeight);
        const offset = Math.floor(index / blockSize) * blockSize;
        if (offset === currentOffset) return;
        currentOffset = offset;
        if (controller) controller.abort();
        if (cache.has(offset)) {
            render(offset, cache.get(offset));
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
        } catch (error) {
            if (error.name === 'AbortError' || currentOffset !== offset) return;
            currentOffset = -1;
            container.setAttribute('aria-busy', 'false');
            retry.hidden = false;
            status.textContent = 'Could not load rows. Use Retry loading rows or scroll to try again.';
        }
    }

    render(0, initial.rows);
    jump.hidden = false;
    jump.addEventListener('submit', (event) => {
        event.preventDefault();
        const input = document.getElementById('result-number');
        if (!input.reportValidity()) return;
        container.scrollTop = (Number(input.value) - 1) * rowHeight;
        container.focus({preventScroll: true});
        update();
    });
    retry.addEventListener('click', () => {
        container.focus({preventScroll: true});
        update();
    });
    // Re-measure after font-size/zoom changes so virtual row positions stay accurate.
    new ResizeObserver(() => {
        const row = body.querySelector('tr:not(.results-spacer)');
        if (!row) return;
        const height = row.getBoundingClientRect().height;
        if (height > 0 && height !== rowHeight) {
            rowHeight = height;
            if (cache.has(currentOffset)) render(currentOffset, cache.get(currentOffset));
        }
    }).observe(table);
    container.addEventListener('scroll', () => {
        clearTimeout(timer);
        timer = setTimeout(update, 60);
    }, {passive: true});
});
