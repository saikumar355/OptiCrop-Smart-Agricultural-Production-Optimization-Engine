import { renderBarChart, renderLineChart, renderPieChart } from './charts.js';

document.addEventListener('DOMContentLoaded', async () => {
    const loaders = document.querySelectorAll('.chart-loader');

    try {
        const response = await fetch('/api/analytics');
        if (!response.ok) throw new Error('Failed to fetch analytics data');

        const data = await response.json();

        // Remove loaders
        loaders.forEach(loader => loader.remove());

        // Model Performance
        const modelLabels = data.model_scores.map(item => item.model);
        const modelScores = data.model_scores.map(item => item.f1_weighted);
        renderBarChart('modelChart', modelLabels, modelScores, 'F1 Score', {
            scales: { y: { min: 0, max: 1 } }
        });

        // Crop Distribution
        const cropLabels = data.crop_distribution.map(item => item.crop);
        const cropCounts = data.crop_distribution.map(item => item.count);
        renderPieChart('cropChart', cropLabels, cropCounts);

        // Volume Chart
        const volLabels = data.daily_volumes.map(item => item.date);
        const volCounts = data.daily_volumes.map(item => item.count);
        renderLineChart('volumeChart', volLabels, volCounts, 'Predictions');

    } catch (error) {
        console.error(error);
        loaders.forEach(loader => {
            loader.innerHTML = '<span style="color:#ba1a1a;font-size:13px;">⚠ Data unavailable.</span>';
        });
    }
});
