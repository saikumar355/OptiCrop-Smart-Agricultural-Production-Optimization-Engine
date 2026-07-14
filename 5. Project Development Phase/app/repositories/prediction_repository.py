import sqlite3
import logging
from typing import List, Optional
from app.models.prediction_record import PredictionRecord

logger = logging.getLogger(__name__)

_DDL_TABLE = """
    CREATE TABLE IF NOT EXISTS predictions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp       TEXT    NOT NULL,
        N               REAL    NOT NULL,
        P               REAL    NOT NULL,
        K               REAL    NOT NULL,
        temperature     REAL    NOT NULL,
        humidity        REAL    NOT NULL,
        rainfall        REAL    NOT NULL,
        ph              REAL    NOT NULL,
        predicted_crop  TEXT    NOT NULL,
        confidence_score REAL   NOT NULL,
        model_name      TEXT    NOT NULL,
        hashed_ip       TEXT    NOT NULL
    )
"""

_DDL_INDEX = """
    CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
    ON predictions (timestamp DESC)
"""


class PredictionRepository:
    """
    SQLite-backed store for PredictionRecord objects.

    Uses a persistent connection for :memory: databases (required because
    each sqlite3.connect(':memory:') call creates a separate, empty database).
    Uses a fresh connection per operation for file-based databases (safer for
    concurrent use with Gunicorn multi-worker deployments).
    """

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._persistent_conn: Optional[sqlite3.Connection] = None
        if db_path == ':memory:':
            self._persistent_conn = sqlite3.connect(
                db_path, check_same_thread=False
            )
            self._persistent_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._persistent_conn is not None:
            return self._persistent_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _release_connection(self, conn: sqlite3.Connection) -> None:
        """Close the connection only if it is not the persistent in-memory one."""
        if conn is not self._persistent_conn:
            conn.close()

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(_DDL_TABLE)
            cursor.execute(_DDL_INDEX)
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database at {self.db_path}: {e}")
            raise
        finally:
            self._release_connection(conn)

    def save(self, record: PredictionRecord) -> None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO predictions (
                    timestamp, N, P, K, temperature, humidity, rainfall, ph,
                    predicted_crop, confidence_score, model_name, hashed_ip
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.timestamp, record.N, record.P, record.K,
                    record.temperature, record.humidity, record.rainfall,
                    record.ph, record.predicted_crop, record.confidence_score,
                    record.model_name, record.hashed_ip,
                ),
            )
            conn.commit()
            record.id = cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save prediction record: {e}")
            raise
        finally:
            self._release_connection(conn)

    def get_paginated(self, page: int, page_size: int) -> List[PredictionRecord]:
        offset = (page - 1) * page_size
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, N, P, K, temperature, humidity, rainfall, ph,
                       predicted_crop, confidence_score, model_name, hashed_ip
                FROM predictions
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (page_size, offset),
            )
            rows = cursor.fetchall()
            return [
                PredictionRecord(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    N=row["N"],
                    P=row["P"],
                    K=row["K"],
                    temperature=row["temperature"],
                    humidity=row["humidity"],
                    rainfall=row["rainfall"],
                    ph=row["ph"],
                    predicted_crop=row["predicted_crop"],
                    confidence_score=row["confidence_score"],
                    model_name=row["model_name"],
                    hashed_ip=row["hashed_ip"],
                )
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Failed to fetch paginated predictions: {e}")
            raise
        finally:
            self._release_connection(conn)

    def count(self) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM predictions")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to count predictions: {e}")
            raise
        finally:
            self._release_connection(conn)

    def delete(self, record_id: int) -> None:
        """Delete a single prediction record by id."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM predictions WHERE id = ?", (record_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to delete prediction record {record_id}: {e}")
            raise
        finally:
            self._release_connection(conn)

    def delete_all(self) -> None:
        """Delete every prediction record (admin bulk-clear)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM predictions")
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear predictions table: {e}")
            raise
        finally:
            self._release_connection(conn)

    # ── Aggregate helpers (used by DashboardService / AnalyticsService) ──────

    def most_recommended_crop(self) -> str | None:
        """Return the crop name with the highest prediction count, or None."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT predicted_crop
                FROM predictions
                GROUP BY predicted_crop
                ORDER BY COUNT(*) DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to query most recommended crop: {e}")
            raise
        finally:
            self._release_connection(conn)

    def average_confidence(self) -> float:
        """Return the mean confidence score across all records, or 0.0."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT AVG(confidence_score) FROM predictions")
            result = cursor.fetchone()[0]
            return float(result) if result is not None else 0.0
        except Exception as e:
            logger.error(f"Failed to query average confidence: {e}")
            raise
        finally:
            self._release_connection(conn)

    def daily_counts(self, days: int = 30) -> list:
        """
        Return a list of {date, count} dicts for the last *days* calendar days,
        ordered ascending by date.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DATE(timestamp) AS day, COUNT(*) AS cnt
                FROM predictions
                WHERE DATE(timestamp) >= DATE('now', ? || ' days')
                GROUP BY day
                ORDER BY day ASC
                """,
                (f"-{days}",),
            )
            return [{"date": row[0], "count": row[1]} for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to query daily counts: {e}")
            raise
        finally:
            self._release_connection(conn)

    def crop_distribution(self) -> list:
        """Return a list of {crop, count} dicts ordered by count descending."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT predicted_crop, COUNT(*) AS cnt
                FROM predictions
                GROUP BY predicted_crop
                ORDER BY cnt DESC
                """
            )
            return [{"crop": row[0], "count": row[1]} for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to query crop distribution: {e}")
            raise
        finally:
            self._release_connection(conn)
