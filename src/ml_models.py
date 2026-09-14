"""Wrapper around ML models for NER extraction."""
import logging
from functools import lru_cache
from typing import Any

from src.config import settings

logger = logging.getLogger(__name__)


class NERModel:
    """Named Entity Recognition model wrapper.

    Uses lazy loading so tests and API startup stay fast.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.ner_model
        self._pipeline: Any = None

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def load(self) -> None:
        """Load the model into memory. Safe to call multiple times."""
        if self._pipeline is not None:
            return

        # Import here to keep startup fast when model isn't needed
        from transformers import pipeline

        logger.info("Loading NER model: %s", self.model_name)
        self._pipeline = pipeline(
            "ner",
            model=self.model_name,
            tokenizer=self.model_name,
            aggregation_strategy="simple",
        )
        logger.info("NER model loaded")

    def extract(self, text: str) -> list[dict[str, Any]]:
        """Extract entities from text.

        Returns a list of dicts with keys:
        entity_type, value, confidence.
        """
        if not self._pipeline:
            self.load()

        if not text.strip():
            return []

        results = self._pipeline(text[:5000])  # limit for safety
        return [
            {
                "entity_type": r["entity_group"],
                "value": r["word"].strip(),
                "confidence": round(float(r["score"]), 4),
            }
            for r in results
            if r["word"].strip()
        ]


@lru_cache
def get_ner_model() -> NERModel:
    """Singleton accessor for the NER model."""
    return NERModel()