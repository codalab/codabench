"""Helpers building the phase leaderboard response (`PhaseViewSet.get_leaderboard`)."""
from collections import Counter


def group_label(name):
    """Display label of a group or queue name: 'comp10__CLB' -> 'CLB', 'APHP' -> 'APHP', '' -> None."""
    if not name:
        return None
    return name.rsplit('__', 1)[-1] or None


def group_labels_by_owner_and_queue(competition):
    """Map (username, queue id) to the label of the participant group sending that user to that queue."""
    labels = {}
    groups = competition.participant_groups.filter(queue__isnull=False).prefetch_related('user_set')
    for group in groups:
        for user in group.user_set.all():
            labels[(user.username, group.queue_id)] = group_label(group.name)
    return labels


def leaderboard_fact_sheet_keys(competition):
    """(key, title) of the fact sheet questions shown on the leaderboard, or None if there are none."""
    fact_sheet = competition.fact_sheet or {}
    keys = [
        (question['key'], question['title'])
        for question in fact_sheet.values()
        if question['is_on_leaderboard'] == 'true'
    ]
    return keys or None


def build_leaderboard_rows(submissions, columns, group_labels):
    """
    Group the serialized leaderboard submissions into leaderboard rows.

    A row is a standalone submission, or the children of a multi-task parent submission
    (shown with the parent ID). When the children ran on several group queues, there is
    one row per group. Scores of columns missing from `columns` (hidden ones) are dropped.

    Returns (rows, has_group_queues).
    """
    visible_indexes = {col['index'] for col in columns}
    children_per_parent_and_task = Counter(
        (s['parent'], s['task']) for s in submissions if s['parent'] is not None
    )
    rows = {}
    has_group_queues = False

    for submission in submissions:
        row_id = submission['parent'] or submission['id']
        queue_id = submission['queue_id']

        label = group_labels.get((submission['owner'], queue_id)) if queue_id else None
        if not label and submission['queue_name']:
            # The serializer gives the queue as '<row_id>_<queue label>'
            label = submission['queue_name'].removeprefix(f'{row_id}_') or None

        # Several children of one parent on the same task, without queue: one row per child
        one_row_per_child = (
            submission['parent'] is not None
            and not queue_id
            and children_per_parent_and_task[(submission['parent'], submission['task'])] > 1
        )
        row_key = (row_id, submission['id'] if one_row_per_child else label)

        if row_key not in rows:
            rows[row_key] = {
                'id': row_id,
                'owner': submission['display_name'] or submission['owner'],
                'scores': [],
                'detailed_results': [],
                'fact_sheet_answers': submission['fact_sheet_answers'],
                'slug_url': submission['slug_url'],
                'organization': submission['organization'],
                'created_when': submission['created_when'],
                'queue_name': f'{row_id}_{label}' if label else None,
            }
            if queue_id or one_row_per_child:
                has_group_queues = True

        row = rows[row_key]
        row['detailed_results'].append({'task': submission['task'], 'id': submission['id']})
        row['scores'].extend(
            {**score, 'task_id': submission['task']}
            for score in submission['scores']
            if score['index'] in visible_indexes
        )

    return list(rows.values()), has_group_queues


def round_scores(rows, columns):
    """Round each score to its column precision, as a string, for display.

    Done last so that rankings use the exact scores. Average rank scores are
    already rounded by `inject_average_ranks`, rounding them again changes nothing.
    """
    precisions = {col['index']: col['precision'] for col in columns}
    for row in rows:
        for score in row['scores']:
            score['score'] = str(round(float(score['score']), precisions[score['index']]))
