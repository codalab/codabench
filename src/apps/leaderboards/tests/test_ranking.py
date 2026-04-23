import pytest
from leaderboards.ranking import fractional_rank, inject_average_ranks


# ---------------------------------------------------------------------------
# fractional_rank
# ---------------------------------------------------------------------------

def test_fractional_rank_no_ties():
    # 3 distinct values → straight 1, 2, 3
    assert fractional_rank([3.0, 1.0, 2.0]) == [3.0, 1.0, 2.0]


def test_fractional_rank_two_way_tie():
    # Positions 1 and 2 are tied → both get 1.5
    assert fractional_rank([1.0, 1.0, 2.0]) == [1.5, 1.5, 3.0]


def test_fractional_rank_three_way_tie():
    # Positions 1, 2, 3 are all tied → mean(1,2,3) = 2.0
    assert fractional_rank([5.0, 5.0, 5.0]) == [2.0, 2.0, 2.0]


def test_fractional_rank_tie_at_end():
    # Two tied at the last positions
    assert fractional_rank([1.0, 2.0, 2.0]) == [1.0, 2.5, 2.5]


def test_fractional_rank_single_element():
    assert fractional_rank([42.0]) == [1.0]


# ---------------------------------------------------------------------------
# Helpers for inject_average_ranks
# ---------------------------------------------------------------------------

def _make_col(index, key, sorting='desc', computation_indexes=None, precision=2, computation='avg_rank'):
    return {
        'id': index,
        'index': index,
        'key': key,
        'title': key,
        'sorting': sorting,
        'computation': computation,
        'computation_indexes': [str(i) for i in (computation_indexes or [])],
        'precision': precision,
        'hidden': False,
    }


def _make_submission(scores):
    """
    scores: list of (column_index, column_key, score_value, task_id)
    """
    return {
        'scores': [
            {'index': idx, 'column_key': key, 'score': str(val), 'task_id': tid, 'is_primary': False}
            for idx, key, val, tid in scores
        ]
    }


# ---------------------------------------------------------------------------
# inject_average_ranks
# ---------------------------------------------------------------------------

def test_inject_average_ranks_basic_values():
    # 3 submissions, 1 descending sub-column (higher = better = rank 1).
    # Scores 0.9, 0.6, 0.3 → ranks 1, 2, 3 → avg_rank 1.0, 2.0, 3.0
    col0 = _make_col(0, 'col0', sorting='desc')
    avg_col = _make_col(2, 'avg_rank', computation_indexes=[0])

    submissions = [
        _make_submission([(0, 'col0', 0.9, 1)]),
        _make_submission([(0, 'col0', 0.6, 1)]),
        _make_submission([(0, 'col0', 0.3, 1)]),
    ]

    col_by_index = {0: col0, 2: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    avg_scores = [
        next(s for s in sub['scores'] if s['column_key'] == 'avg_rank')
        for sub in submissions
    ]
    assert float(avg_scores[0]['score']) == 1.0
    assert float(avg_scores[1]['score']) == 2.0
    assert float(avg_scores[2]['score']) == 3.0


def test_inject_average_ranks_with_ties():
    # Two submissions tied on the sub-column → both get fractional rank 1.5
    col0 = _make_col(0, 'col0', sorting='desc')
    avg_col = _make_col(1, 'avg_rank', computation_indexes=[0])

    submissions = [
        _make_submission([(0, 'col0', 0.8, 1)]),
        _make_submission([(0, 'col0', 0.8, 1)]),
        _make_submission([(0, 'col0', 0.5, 1)]),
    ]

    col_by_index = {0: col0, 1: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    avg_scores = [
        float(next(s for s in sub['scores'] if s['column_key'] == 'avg_rank')['score'])
        for sub in submissions
    ]
    assert avg_scores[0] == 1.5
    assert avg_scores[1] == 1.5
    assert avg_scores[2] == 3.0


def test_inject_average_ranks_ascending_column():
    # Ascending column: lower score = better = rank 1
    col0 = _make_col(0, 'col0', sorting='asc')
    avg_col = _make_col(1, 'avg_rank', computation_indexes=[0])

    submissions = [
        _make_submission([(0, 'col0', 0.1, 1)]),  # lowest → rank 1
        _make_submission([(0, 'col0', 0.5, 1)]),  # rank 2
        _make_submission([(0, 'col0', 0.9, 1)]),  # highest → rank 3
    ]

    col_by_index = {0: col0, 1: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    avg_scores = [
        float(next(s for s in sub['scores'] if s['column_key'] == 'avg_rank')['score'])
        for sub in submissions
    ]
    assert avg_scores[0] == 1.0
    assert avg_scores[1] == 2.0
    assert avg_scores[2] == 3.0


def test_inject_average_ranks_missing_score_gets_worst_rank():
    # Submission without a score on the sub-column gets rank n (=3 here)
    col0 = _make_col(0, 'col0', sorting='desc')
    avg_col = _make_col(1, 'avg_rank', computation_indexes=[0])

    submissions = [
        _make_submission([(0, 'col0', 0.9, 1)]),   # rank 1
        _make_submission([(0, 'col0', 0.5, 1)]),   # rank 2
        _make_submission([]),                       # no score → rank 3
    ]

    col_by_index = {0: col0, 1: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    avg_scores = [
        float(next(s for s in sub['scores'] if s['column_key'] == 'avg_rank')['score'])
        for sub in submissions
    ]
    assert avg_scores[0] == 1.0
    assert avg_scores[1] == 2.0
    assert avg_scores[2] == 3.0  # worst rank = n = 3


def test_inject_average_ranks_two_subcolumns():
    # Average over two sub-columns
    col0 = _make_col(0, 'col0', sorting='desc')
    col1 = _make_col(1, 'col1', sorting='desc')
    avg_col = _make_col(2, 'avg_rank', computation_indexes=[0, 1])

    # Sub0: col0=0.9 (rank1), col1=0.3 (rank3) → avg 2.0
    # Sub1: col0=0.6 (rank2), col1=0.6 (rank2) → avg 2.0
    # Sub2: col0=0.3 (rank3), col1=0.9 (rank1) → avg 2.0
    submissions = [
        _make_submission([(0, 'col0', 0.9, 1), (1, 'col1', 0.3, 1)]),
        _make_submission([(0, 'col0', 0.6, 1), (1, 'col1', 0.6, 1)]),
        _make_submission([(0, 'col0', 0.3, 1), (1, 'col1', 0.9, 1)]),
    ]

    col_by_index = {0: col0, 1: col1, 2: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    avg_scores = [
        float(next(s for s in sub['scores'] if s['column_key'] == 'avg_rank')['score'])
        for sub in submissions
    ]
    assert avg_scores[0] == 2.0
    assert avg_scores[1] == 2.0
    assert avg_scores[2] == 2.0


def test_inject_average_ranks_task_id_propagation():
    # The injected score must carry the same task_id as existing scores so the
    # frontend can match it via (task_id, column_key).
    col0 = _make_col(0, 'col0', sorting='desc')
    avg_col = _make_col(1, 'avg_rank', computation_indexes=[0])

    task_id = 99
    submissions = [
        _make_submission([(0, 'col0', 0.9, task_id)]),
        _make_submission([(0, 'col0', 0.5, task_id)]),
    ]

    col_by_index = {0: col0, 1: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    for sub in submissions:
        injected = [s for s in sub['scores'] if s['column_key'] == 'avg_rank']
        assert len(injected) == 1
        assert injected[0]['task_id'] == task_id


def test_inject_average_ranks_multi_task_injects_one_per_task():
    # Multi-task submissions have scores with different task_ids.
    # One avg_rank entry must be injected per task_id.
    col0 = _make_col(0, 'col0', sorting='desc')
    avg_col = _make_col(1, 'avg_rank', computation_indexes=[0])

    submissions = [
        _make_submission([(0, 'col0', 0.9, 10), (0, 'col0', 0.8, 20)]),
        _make_submission([(0, 'col0', 0.5, 10), (0, 'col0', 0.4, 20)]),
    ]

    col_by_index = {0: col0, 1: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=0)

    for sub in submissions:
        injected = [s for s in sub['scores'] if s['column_key'] == 'avg_rank']
        injected_task_ids = {s['task_id'] for s in injected}
        assert injected_task_ids == {10, 20}


def test_inject_average_ranks_sorts_by_primary_avg_rank():
    # When the avg_rank column is the primary, submissions are re-sorted
    # ascending (rank 1 = best position = first row).
    col0 = _make_col(0, 'col0', sorting='desc')
    avg_col = _make_col(1, 'avg_rank', sorting='asc', computation_indexes=[0])

    # Scores: 0.3 → rank3, 0.9 → rank1, 0.6 → rank2
    # After sort ascending by avg_rank: rank1 first, then rank2, then rank3
    submissions = [
        _make_submission([(0, 'col0', 0.3, 1)]),  # will become rank 3
        _make_submission([(0, 'col0', 0.9, 1)]),  # will become rank 1
        _make_submission([(0, 'col0', 0.6, 1)]),  # will become rank 2
    ]

    col_by_index = {0: col0, 1: avg_col}
    inject_average_ranks(submissions, [avg_col], col_by_index, primary_index=1)

    avg_scores = [
        float(next(s for s in sub['scores'] if s['column_key'] == 'avg_rank')['score'])
        for sub in submissions
    ]
    assert avg_scores == [1.0, 2.0, 3.0]


def test_inject_average_ranks_no_avg_rank_cols_is_noop():
    submissions = [_make_submission([(0, 'col0', 0.9, 1)])]
    original_scores = list(submissions[0]['scores'])

    inject_average_ranks(submissions, [], {}, primary_index=0)

    assert submissions[0]['scores'] == original_scores
