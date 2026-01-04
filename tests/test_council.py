"""Tests for core council logic functions."""

import pytest
from backend.council import parse_ranking_from_text, calculate_aggregate_rankings


class TestParseRankingFromText:
    """Tests for parse_ranking_from_text function."""

    def test_standard_format_with_header(self):
        """Test parsing with proper FINAL RANKING: header and numbered list."""
        text = """Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B"""

        result = parse_ranking_from_text(text)
        assert result == ["Response C", "Response A", "Response B"]

    def test_standard_format_no_spaces_after_period(self):
        """Test parsing when there's no space after the period."""
        text = """Some evaluation text...

FINAL RANKING:
1.Response A
2.Response C
3.Response B"""

        result = parse_ranking_from_text(text)
        assert result == ["Response A", "Response C", "Response B"]

    def test_extended_ranking_more_than_three(self):
        """Test parsing with more than 3 responses."""
        text = """Evaluation text...

FINAL RANKING:
1. Response D
2. Response A
3. Response C
4. Response B
5. Response E"""

        result = parse_ranking_from_text(text)
        assert result == ["Response D", "Response A", "Response C", "Response B", "Response E"]

    def test_fallback_without_header(self):
        """Test fallback parsing when FINAL RANKING: header is missing."""
        text = """After careful analysis:
Response B is the best
Response A is second
Response C is third"""

        result = parse_ranking_from_text(text)
        # Should extract Response patterns in order they appear
        assert result == ["Response B", "Response A", "Response C"]

    def test_fallback_finds_responses_in_paragraph(self):
        """Test fallback when responses are mentioned inline."""
        text = "I think Response C is best, followed by Response A and then Response B."

        result = parse_ranking_from_text(text)
        assert result == ["Response C", "Response A", "Response B"]

    def test_no_response_patterns_returns_empty(self):
        """Test that empty list is returned when no Response patterns found."""
        text = "This text has no response patterns at all."

        result = parse_ranking_from_text(text)
        assert result == []

    def test_empty_string_returns_empty(self):
        """Test that empty string returns empty list."""
        result = parse_ranking_from_text("")
        assert result == []

    def test_only_header_no_rankings(self):
        """Test with FINAL RANKING header but no actual rankings."""
        text = """Some evaluation...

FINAL RANKING:
No valid rankings here."""

        result = parse_ranking_from_text(text)
        assert result == []

    def test_extra_text_after_ranking(self):
        """Test that extra text after ranking section is handled."""
        text = """Evaluation...

FINAL RANKING:
1. Response A
2. Response B
3. Response C

Some additional notes that shouldn't affect parsing."""

        result = parse_ranking_from_text(text)
        assert result == ["Response A", "Response B", "Response C"]

    def test_lowercase_final_ranking_not_matched(self):
        """Test that lowercase 'final ranking:' doesn't trigger header matching."""
        text = """final ranking:
1. Response A
2. Response B"""

        result = parse_ranking_from_text(text)
        # Should fall back to pattern matching since header is case-sensitive
        assert result == ["Response A", "Response B"]

    def test_multiple_response_mentions_same_label(self):
        """Test when the same response is mentioned multiple times."""
        text = """Response A is good. Response A really stands out.
Response B is okay.

FINAL RANKING:
1. Response A
2. Response B"""

        result = parse_ranking_from_text(text)
        # Should only extract from FINAL RANKING section
        assert result == ["Response A", "Response B"]

    def test_response_labels_beyond_z(self):
        """Test with single-letter labels up to Z."""
        text = """FINAL RANKING:
1. Response Z
2. Response Y
3. Response X"""

        result = parse_ranking_from_text(text)
        assert result == ["Response Z", "Response Y", "Response X"]


class TestCalculateAggregateRankings:
    """Tests for calculate_aggregate_rankings function."""

    def test_basic_aggregation(self):
        """Test basic ranking aggregation with dict format label_to_model."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": """Evaluation text...

FINAL RANKING:
1. Response A
2. Response B
3. Response C"""
            },
            {
                "model": "model-2",
                "instance": 1,
                "ranking": """Evaluation text...

FINAL RANKING:
1. Response B
2. Response A
3. Response C"""
            }
        ]

        label_to_model = {
            "Response A": {"model": "gpt-4", "instance": 1},
            "Response B": {"model": "claude-3", "instance": 1},
            "Response C": {"model": "gemini", "instance": 1},
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Both models ranked, average positions:
        # gpt-4: positions 1, 2 -> avg 1.5
        # claude-3: positions 2, 1 -> avg 1.5
        # gemini: positions 3, 3 -> avg 3.0

        assert len(result) == 3
        # First two should have avg 1.5 (tie), gemini should be last with 3.0
        assert result[2]["model"] == "gemini"
        assert result[2]["average_rank"] == 3.0
        assert result[2]["rankings_count"] == 2

    def test_with_duplicate_instances(self):
        """Test aggregation when models have duplicate instances."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response A
2. Response B"""
            }
        ]

        label_to_model = {
            "Response A": {"model": "gpt-4", "instance": 1},
            "Response B": {"model": "gpt-4", "instance": 2},
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        assert len(result) == 2
        # Instance 1 ranked 1st, instance 2 ranked 2nd
        assert result[0]["model"] == "gpt-4"
        assert result[0]["instance"] == 1
        assert result[0]["average_rank"] == 1.0
        assert result[1]["model"] == "gpt-4"
        assert result[1]["instance"] == 2
        assert result[1]["average_rank"] == 2.0

    def test_legacy_string_format_label_to_model(self):
        """Test backwards compatibility with old string format label_to_model."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response A
2. Response B"""
            }
        ]

        # Old format: label maps directly to model string
        label_to_model = {
            "Response A": "gpt-4",
            "Response B": "claude-3",
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        assert len(result) == 2
        assert result[0]["model"] == "gpt-4"
        assert result[0]["instance"] == 1  # Default instance
        assert result[0]["average_rank"] == 1.0
        assert result[1]["model"] == "claude-3"
        assert result[1]["average_rank"] == 2.0

    def test_empty_stage2_results(self):
        """Test with empty stage2 results."""
        result = calculate_aggregate_rankings([], {})
        assert result == []

    def test_unparseable_rankings(self):
        """Test when rankings can't be parsed (no Response patterns)."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": "This ranking has no valid patterns."
            }
        ]

        label_to_model = {
            "Response A": {"model": "gpt-4", "instance": 1},
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)
        assert result == []

    def test_partial_rankings(self):
        """Test when some models only rank subset of responses."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response A
2. Response B
3. Response C"""
            },
            {
                "model": "model-2",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response A
2. Response C"""
                # Note: Response B is missing from this ranking
            }
        ]

        label_to_model = {
            "Response A": {"model": "gpt-4", "instance": 1},
            "Response B": {"model": "claude-3", "instance": 1},
            "Response C": {"model": "gemini", "instance": 1},
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # gpt-4: positions 1, 1 -> avg 1.0, count 2
        # claude-3: position 2 -> avg 2.0, count 1
        # gemini: positions 3, 2 -> avg 2.5, count 2

        gpt4 = next(r for r in result if r["model"] == "gpt-4")
        claude3 = next(r for r in result if r["model"] == "claude-3")
        gemini = next(r for r in result if r["model"] == "gemini")

        assert gpt4["average_rank"] == 1.0
        assert gpt4["rankings_count"] == 2
        assert claude3["average_rank"] == 2.0
        assert claude3["rankings_count"] == 1
        assert gemini["average_rank"] == 2.5
        assert gemini["rankings_count"] == 2

    def test_unknown_label_ignored(self):
        """Test that unknown labels in rankings are ignored."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response A
2. Response X
3. Response B"""
                # Response X is not in label_to_model
            }
        ]

        label_to_model = {
            "Response A": {"model": "gpt-4", "instance": 1},
            "Response B": {"model": "claude-3", "instance": 1},
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # Response X should be ignored, A gets position 1, B gets position 3
        assert len(result) == 2
        gpt4 = next(r for r in result if r["model"] == "gpt-4")
        claude3 = next(r for r in result if r["model"] == "claude-3")

        assert gpt4["average_rank"] == 1.0
        assert claude3["average_rank"] == 3.0

    def test_sorting_by_average_rank(self):
        """Test that results are sorted by average rank (best first)."""
        stage2_results = [
            {
                "model": "model-1",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response C
2. Response A
3. Response B"""
            },
            {
                "model": "model-2",
                "instance": 1,
                "ranking": """FINAL RANKING:
1. Response C
2. Response B
3. Response A"""
            }
        ]

        label_to_model = {
            "Response A": {"model": "gpt-4", "instance": 1},
            "Response B": {"model": "claude-3", "instance": 1},
            "Response C": {"model": "gemini", "instance": 1},
        }

        result = calculate_aggregate_rankings(stage2_results, label_to_model)

        # gemini: avg 1.0 (1st place)
        # claude-3: avg 2.5 (2nd place)
        # gpt-4: avg 2.5 (tied for 2nd)

        assert result[0]["model"] == "gemini"
        assert result[0]["average_rank"] == 1.0


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_parse_ranking_with_extra_whitespace(self):
        """Test parsing handles extra whitespace gracefully."""
        text = """FINAL RANKING:

  1.   Response A
  2. Response B
  3.Response C  """

        result = parse_ranking_from_text(text)
        assert result == ["Response A", "Response B", "Response C"]

    def test_real_world_evaluation_format(self):
        """Test with a realistic evaluation response format."""
        text = """## Evaluation

**Response A Analysis:**
This response provides comprehensive coverage of the topic with accurate information.
It includes good examples and clear explanations. However, it could be more concise.

**Response B Analysis:**
While technically accurate, this response lacks depth and misses some important nuances.
The explanation could benefit from more examples.

**Response C Analysis:**
This is the most thorough response, covering all aspects of the question with excellent
examples and clear reasoning. Minor issue with formatting.

## Summary
Response C provides the best overall answer due to its comprehensiveness and clarity.
Response A is a close second with good coverage.
Response B, while accurate, lacks the depth of the other responses.

FINAL RANKING:
1. Response C
2. Response A
3. Response B"""

        result = parse_ranking_from_text(text)
        assert result == ["Response C", "Response A", "Response B"]
