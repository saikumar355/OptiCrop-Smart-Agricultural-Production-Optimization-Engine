from app.repositories.prediction_repository import PredictionRepository
from typing import Dict, Any


class DashboardService:
    def __init__(self, repo: PredictionRepository) -> None:
        self.repo = repo

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Return dashboard KPIs.  All aggregation is delegated to the repository
        (SQL GROUP BY / AVG), so this service never page-fetches records.
        """
        total = self.repo.count()
        most_recommended = self.repo.most_recommended_crop() or "N/A"
        avg_confidence = self.repo.average_confidence()
        daily_counts = self.repo.daily_counts(days=30)

        return {
            "total_predictions": total,
            "most_recommended_crop": most_recommended,
            "avg_confidence": round(avg_confidence, 3),
            "daily_counts": daily_counts,
        }
