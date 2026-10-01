from leaderboards.models import Column


def fractional_rank(values):
    """
    Fractional (average) ranking: tied values receive the mean of the ranks they
    would occupy, identical to scipy.stats.rankdata(method='average').
    Rank 1 is assigned to the smallest value.
    """
    sorted_vals = sorted(values)
    rank_sum = {}
    rank_count = {}
    for rank, val in enumerate(sorted_vals, start=1):
        rank_sum[val] = rank_sum.get(val, 0) + rank
        rank_count[val] = rank_count.get(val, 0) + 1
    return [rank_sum[v] / rank_count[v] for v in values]


def inject_average_ranks(submissions, avg_rank_cols, col_by_index, primary_index):
    """
    For each AVERAGE_RANK column, rank submissions on each referenced sub-column
    using fractional (average) ranking, compute the mean rank per submission, and
    append it as a synthetic score entry.
    If the primary column is AVERAGE_RANK, re-sort the list in-place afterward.

    Fractional ranking: tied submissions share the mean of the ranks they occupy
    (e.g. two entries tying for positions 2 and 3 both receive rank 2.5).
    Submissions missing a score for a sub-column are placed last (rank = n).
    When a submission has multiple scores for the same column (multi-task), they are
    summed before ranking, consistent with the ORM annotation in the serializer.
    """
    # Pre-aggregate scores per submission per column (sum across tasks).
    submission_col_scores = []
    for sub in submissions:
        col_scores = {}
        for s in sub['scores']:
            idx = s['index']
            try:
                val = float(s['score'])
            except (ValueError, TypeError):
                val = None
            if idx not in col_scores:
                col_scores[idx] = val
            elif val is not None:
                col_scores[idx] = (col_scores[idx] or 0) + val
        submission_col_scores.append(col_scores)

    n = len(submissions)

    for col in avg_rank_cols:
        if not col.get('computation_indexes'):
            continue
        sub_indices = [int(i) for i in col['computation_indexes']]

        per_column_ranks = []
        for sub_idx in sub_indices:
            sub_col = col_by_index.get(sub_idx)
            if sub_col is None:
                continue

            valid_indices = [i for i in range(n) if submission_col_scores[i].get(sub_idx) is not None]
            valid_scores = [submission_col_scores[i][sub_idx] for i in valid_indices]

            if not valid_scores:
                continue

            # Negate descending columns so rank 1 = highest score.
            scores_for_rank = [-s for s in valid_scores] if sub_col['sorting'] == 'desc' else valid_scores
            fractions = fractional_rank(scores_for_rank)

            ranks = {i: float(n) for i in range(n)}  # default: worst rank for unscored
            for pos, sub_i in enumerate(valid_indices):
                ranks[sub_i] = fractions[pos]
            per_column_ranks.append(ranks)

        if not per_column_ranks:
            continue

        is_primary = col['index'] == primary_index
        for i, sub in enumerate(submissions):
            sub_ranks = [r[i] for r in per_column_ranks]
            avg_rank = sum(sub_ranks) / len(sub_ranks)
            score_entry = {
                'index': col['index'],
                'column_key': col['key'],
                'score': str(round(avg_rank, col.get('precision', 2))),
                'is_primary': is_primary,
            }
            # The frontend matches scores by (task_id, column_key). Average rank is
            # cross-task, so inject one copy per task that already has scores here.
            task_ids = {s['task_id'] for s in sub['scores'] if s.get('task_id') is not None}
            for task_id in task_ids:
                sub['scores'].append({**score_entry, 'task_id': task_id})

    primary_col = col_by_index.get(primary_index)
    if primary_col and primary_col.get('computation') == Column.AVERAGE_RANK:
        reverse = primary_col['sorting'] == 'desc'

        def _sort_key(sub):
            for s in sub['scores']:
                if s['index'] == primary_index:
                    try:
                        return float(s['score'])
                    except (ValueError, TypeError):
                        pass
            return float('inf') if not reverse else float('-inf')

        submissions.sort(key=_sort_key, reverse=reverse)
