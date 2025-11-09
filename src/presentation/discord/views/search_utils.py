from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from domain import Template


@dataclass
class TemplateSearchEntry:
    template: Template
    score: float
    matched_keywords: list[str]


def search_templates(
    templates: Iterable[Template],
    query: str,
) -> list[TemplateSearchEntry]:
    """テンプレートのリストから検索クエリに一致する候補を返す。"""

    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return []

    keywords = [token for token in re.split(r"\s+", normalized_query) if token]

    entries: list[TemplateSearchEntry] = []
    for template in templates:
        title = str(template.title or "")
        choices = [str(choice) for choice in (template.choices or [])]
        text_candidates = [title] + choices
        lower_texts = [text.lower() for text in text_candidates if text]
        concatenated = " ".join(lower_texts)

        ratios = [_fuzzy_ratio(normalized_query, text) for text in lower_texts]
        if concatenated:
            ratios.append(_fuzzy_ratio(normalized_query, concatenated))
        base_score = max(ratios) if ratios else 0.0

        substring_bonus = 0.25 if normalized_query and normalized_query in concatenated else 0.0
        matched_keywords = [token for token in keywords if token in concatenated]
        keyword_bonus = 0.15 * len(matched_keywords)

        if keywords:
            token_scores = [
                max(_fuzzy_ratio(token, text) for text in lower_texts)
                if lower_texts
                else 0.0
                for token in keywords
            ]
            token_bonus = sum(token_scores) / max(len(keywords), 1) * 0.2
        else:
            token_bonus = 0.0

        score = base_score + substring_bonus + keyword_bonus + token_bonus
        if score <= 0.2 and not matched_keywords:
            continue

        entries.append(
            TemplateSearchEntry(
                template=template,
                score=round(score, 4),
                matched_keywords=matched_keywords,
            )
        )

    entries.sort(key=lambda entry: entry.score, reverse=True)
    return entries


def _fuzzy_ratio(lhs: str, rhs: str) -> float:
    if not lhs or not rhs:
        return 0.0
    return SequenceMatcher(a=lhs, b=rhs).ratio()


__all__ = ["TemplateSearchEntry", "search_templates"]
