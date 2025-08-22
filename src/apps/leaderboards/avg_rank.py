# Utilities for average rank computation
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
import ranky as rk

def compute_avg_rank(phase, comp_column, precision=2, missing_policy='ignore'):
    base_idxs = [int(i) for i in comp_column.computation_indexes.split(',') if i.strip()]
    base_cols = list(comp_column.leaderboard.columns.filter(index__in=base_idxs).order_by('index'))
    subs = list(phase.submissions.all().prefetch_related('scores','scores__column'))
    n_subs, n_cols = len(subs), len(base_cols)
    M = np.full((n_subs, n_cols), np.nan, float)

    col_id_to_j = {c.id: j for j, c in enumerate(base_cols)}
    sub_id_to_i = {s.id: i for i, s in enumerate(subs)}

    for s in subs:
        for sc in s.scores.all():
            j = col_id_to_j.get(sc.column_id)
            if j is None: continue
            M[sub_id_to_i[s.id], j] = float(sc.score)

    # reverse per column (True if 'asc')
    reverse = [c.sorting == 'asc' for c in base_cols]

    # manage missing values
    if missing_policy == 'worst':
        M = np.where(np.isnan(M), np.nanmin(M) - 1.0, M)  # pousse sous le pire

    # ranky: axis=1 (score = coluns), method='mean' --> average rank
    avg_rank = rk.average_rank(M, axis=1, method='mean', reverse=reverse)

    from .models import SubmissionScore
    q = Decimal(10) ** -precision
    for s in subs:
        val = avg_rank[sub_id_to_i[s.id]]
        if np.isnan(val):
            try:
                s.scores.get(column=comp_column).delete()
            except SubmissionScore.DoesNotExist:
                pass
            continue
        d = Decimal(val).quantize(q, rounding=ROUND_HALF_UP)
        try:
            ss = s.scores.get(column=comp_column)
            ss.score = d
            ss.save()
        except SubmissionScore.DoesNotExist:
            ss = SubmissionScore.objects.create(column=comp_column, score=d)
            s.scores.add(ss)