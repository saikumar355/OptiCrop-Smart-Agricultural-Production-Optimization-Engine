import { renderLineChart } from './charts.js';

document.addEventListener('DOMContentLoaded', async () => {
    const kpiTotal = document.getElementById('kpi-total');
    const kpiCrop = document.getElementById('kpi-crop');
    const kpiConf = document.getElementById('kpi-conf');
    const loader = document.getElementById('chart-loader');

    try {
        const response = await fetch('/api/dashboard');
        if (!response.ok) throw new Error('Failed to fetch dashboard data');

        const data = await response.json();

        // Remove skeleton class and set values
        if (kpiTotal) { kpiTotal.classList.remove('skeleton'); kpiTotal.textContent = data.total_predictions.toLocaleString(); }
        if (kpiCrop) { kpiCrop.classList.remove('skeleton'); kpiCrop.textContent = data.most_recommended_crop; }
        if (kpiConf) { kpiConf.classList.remove('skeleton'); kpiConf.textContent = `${(data.avg_confidence * 100).toFixed(1)}%`; }

        // Render Chart
        if (loader) loader.remove();

        const labels = data.daily_counts.map(item => item.date);
        const counts = data.daily_counts.map(item => item.count);

        renderLineChart('activityChart', labels, counts, 'Predictions');

    } catch (error) {
        console.error(error);

        const errHtml = '<span style="color:#ba1a1a;font-size:13px;">⚠ Error</span>';

        if (kpiTotal) { kpiTotal.classList.remove('skeleton'); kpiTotal.innerHTML = errHtml; }
        if (kpiCrop) { kpiCrop.classList.remove('skeleton'); kpiCrop.innerHTML = errHtml; }
        if (kpiConf) { kpiConf.classList.remove('skeleton'); kpiConf.innerHTML = errHtml; }

        if (loader) {
            loader.innerHTML = '<span style="color:#ba1a1a;font-size:13px;">⚠ Failed to load chart data.</span>';
        }
    }
});
