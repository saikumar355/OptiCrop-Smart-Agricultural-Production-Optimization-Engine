function isChartjsLoaded() {
    return typeof Chart !== 'undefined';
}

function showFallback(canvasId, message = 'Chart is currently unavailable.') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const parent = canvas.parentElement;

    const fallbackDiv = document.createElement('div');
    fallbackDiv.style.cssText = 'display:flex;align-items:center;justify-content:center;min-height:200px;color:#717a6d;font-size:14px;gap:8px;';
    fallbackDiv.innerHTML = `<span class="material-symbols-outlined">bar_chart</span> ${message}`;

    canvas.style.display = 'none';
    parent.appendChild(fallbackDiv);
    return null;
}

export function renderBarChart(canvasId, labels, data, label, options = {}) {
    if (!isChartjsLoaded()) return showFallback(canvasId);

    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: 'rgba(0, 69, 13, 0.7)',
                borderColor: '#00450d',
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { font: { family: 'Inter' }, color: '#41493e' } }
            },
            scales: {
                x: { ticks: { font: { family: 'Inter' }, color: '#41493e' }, grid: { color: 'rgba(192,201,187,0.3)' } },
                y: { ticks: { font: { family: 'Inter' }, color: '#41493e' }, grid: { color: 'rgba(192,201,187,0.3)' } }
            },
            ...options
        }
    });
}

export function renderLineChart(canvasId, labels, data, label, options = {}) {
    if (!isChartjsLoaded()) return showFallback(canvasId);

    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                fill: true,
                backgroundColor: 'rgba(0, 69, 13, 0.08)',
                borderColor: '#00450d',
                pointBackgroundColor: '#006e1c',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { font: { family: 'Inter' }, color: '#41493e' } }
            },
            scales: {
                x: { ticks: { font: { family: 'Inter' }, color: '#41493e' }, grid: { color: 'rgba(192,201,187,0.3)' } },
                y: { ticks: { font: { family: 'Inter' }, color: '#41493e' }, grid: { color: 'rgba(192,201,187,0.3)' } }
            },
            ...options
        }
    });
}

export function renderPieChart(canvasId, labels, data, options = {}) {
    if (!isChartjsLoaded()) return showFallback(canvasId);

    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const colors = [
        '#00450d', '#006e1c', '#ffb957', '#1b5e20', '#ffddb5',
        '#41493e', '#91f78e', '#717a6d', '#c0c9bb', '#533400'
    ];

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, data.length),
                borderColor: '#ffffff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { font: { family: 'Inter', size: 12 }, color: '#41493e', padding: 16 }
                }
            },
            ...options
        }
    });
}
