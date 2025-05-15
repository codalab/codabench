import datetime

from django.utils import timezone

v15_yaml_data = {
    "title": "Sample time series competition",
    "description": "Sample competition for time series prediction",
    "image": "logo.jpg",
    "competition_docker_image": "codalab/codalab-legacy:py37",
    "end_date": None,
    "html": {
        "data": "data.txt",
        "terms": "terms.txt",
    },
    "phases": {
        "1": {
            "phasenumber": 1,
            "label": "Development Phase",
            "description": "Development phase",
            "start_date": "2019-01-01",
            "execution_time_limit": 500,
            "max_submissions_per_day": 5,
            "max_submissions_per_person": 100,
            "ingestion_program": "ingestion_program.zip",
            "input_data": "evaluation_data.zip",
            "scoring_program": "scoring_program.zip",
            "reference_data": "evaluation_data.zip",
        },
        "2": {
            "phasenumber": 2,
            "label": "Final Phase",
            "description": "Final phase",
            "start_date": "2019-09-30",
            "execution_time_limit": 300,
            "max_submissions_per_day": 5,
            "max_submissions_per_person": 100,
            "auto_migration": True,
            "ingestion_program": "ingestion_program.zip",
            "input_data": "evaluation_data.zip",
            "scoring_program": "scoring_program.zip",
            "reference_data": "evaluation_data.zip",
        }
    },
    "leaderboard": {
        "leaderboards": {
            "Results": {
                "label": "RESULTS",
                "rank": 1
            }
        },
        "columns": {
            "prediction_score": {
                "leaderboard": {
                    "label": "RESULTS",
                    "rank": 1
                },
                "label": "Prediction score",
                "numeric_format": 4,
                "rank": 1
            },
            "Duration": {
                "leaderboard": {
                    "label": "RESULTS",
                    "rank": 1
                },
                "label": "Duration",
                "numeric_format": 2,
                "rank": 2
            }
        }
    }
}

v2_yaml_data = {
    "title": "Sample time series competition",
    "description": "Sample competition for time series prediction",
    "image": "logo.jpg",
    "terms": "terms.txt",
    "pages": [{
        "title": "data",
        "file": "data.txt"
    }],
    "tasks": [
        {
            "index": 0,
            "name": "Development Phase Task",
            "description": "Development phase",
            "ingestion_program": "ingestion_program.zip",
            "input_data": "evaluation_data.zip",
            "scoring_program": "scoring_program.zip",
            "reference_data": "evaluation_data.zip"
        },
        {
            "index": 1,
            "name": "Final Phase Task",
            "description": "Final phase",
            "ingestion_program": "ingestion_program.zip",
            "input_data": "evaluation_data.zip",
            "scoring_program": "scoring_program.zip",
            "reference_data": "evaluation_data.zip"
        }
    ],

    "phases": [
        {
            "name": "Development Phase",
            "description": "Development phase",
            "execution_time_limit": 500,
            "max_submissions_per_day": 5,
            "max_submissions_per_person": 100,
            "start": "2019-01-01",
            "end": "2019-09-29",
            "tasks": [0]
        },
        {
            "name": "Final Phase",
            "description": "Final phase",
            "execution_time_limit": 300,
            "max_submissions_per_day": 5,
            "max_submissions_per_person": 100,
            "auto_migrate_to_this_phase": True,
            "start": "2019-09-30",
            "tasks": [1]
        }
    ],
    "leaderboards": [{
        "title": "Results",
        "key": "Results",
        "columns": [
            {
                "title": "prediction_score",
                "key": "prediction_score",
                "index": 0,
                "sorting": "desc"
            },
            {
                "title": "Duration",
                "key": "Duration",
                "index": 1,
                "sorting": "desc"
            }
        ]
    }]
}

# -------------------------------------------------
# Truth Data
# -------------------------------------------------

V1_LEADERBOARDS = [{
    "title": "Results",
    "key": "Results",
    "label": "RESULTS",
    "columns": [
        {
            "title": "Prediction score",
            "key": "prediction_score",
            "index": 0,
            "sorting": "desc",
            "precision": 4,
            "hidden": False,
        },
        {
            "title": "Duration",
            "key": "Duration",
            "index": 1,
            "sorting": "desc",
            "precision": 2,
            "hidden": False,
        }
    ]
}]

V2_LEADERBOARDS = [{
    "title": "Results",
    "key": "Results",
    "columns": [
        {
            "title": "prediction_score",
            "key": "prediction_score",
            "index": 0,
            "sorting": "desc"
        },
        {
            "title": "Duration",
            "key": "Duration",
            "index": 1,
            "sorting": "desc"
        }
    ]
}]

PAGES = [{
    "title": "data",
    "content": "Placeholder data content for testing\n",
    "index": 0
}]
TERMS = 'Placeholder terms content for testing\n'

PHASES = [
    {
        'index': 0,
        'start': datetime.datetime(2019, 1, 1, 0, 0, tzinfo=timezone.now().tzinfo),
        'name': 'Development Phase',
        'description': 'Development phase',
        'execution_time_limit': 500,
        'max_submissions_per_day': 5,
        'max_submissions_per_person': 100,
        'auto_migrate_to_this_phase': False,
        'has_max_submissions': True,
        'end': datetime.datetime(2019, 9, 29, 0, 0, tzinfo=timezone.now().tzinfo),
        'public_data': None,
        'starting_kit': None,
        'tasks': [0],
        'status': 'Previous',
        'hide_output': False,
        'hide_prediction_output': False,
        'hide_score_output': False,
    },
    {
        'index': 1,
        'start': datetime.datetime(2019, 9, 30, 0, 0, tzinfo=timezone.now().tzinfo),
        'name': 'Final Phase',
        'description': 'Final phase',
        'execution_time_limit': 300,
        'max_submissions_per_day': 5,
        'max_submissions_per_person': 100,
        'auto_migrate_to_this_phase': True,
        'has_max_submissions': True,
        'end': None,
        'public_data': None,
        'starting_kit': None,
        'tasks': [1],
        'status': 'Current',
        'is_final_phase': True,
        'hide_output': False,
        'hide_prediction_output': False,
        'hide_score_output': False,
    }
]


def get_phases(version):
    if version == 1:
        return PHASES
    elif version == 2:
        # Make a copy of the list so we aren't mutating the original phases object. May not be strictly necessary,
        # but if we ever write a test comparing v1 to v2 or something, this would avoid bugs.
        v2 = [{k: v for k, v in phase.items()} for phase in PHASES]
        return v2


def get_tasks(user_id):
    return {
        0: {
            'name': 'Development Phase Task',
            'description': 'Development phase',
            'created_by': user_id,
            'ingestion_only_during_scoring': False,
            'ingestion_program': {
                'file_name': 'ingestion_program.zip',
                'file_path': '/app/src/apps/competitions/tests/files/ingestion_program.zip',
                'file_type': 'ingestion_program',
                'creator': user_id
            },
            'input_data': {
                'file_name': 'evaluation_data.zip',
                'file_path': '/app/src/apps/competitions/tests/files/evaluation_data.zip',
                'file_type': 'input_data',
                'creator': user_id
            },
            'scoring_program': {
                'file_name': 'scoring_program.zip',
                'file_path': '/app/src/apps/competitions/tests/files/scoring_program.zip',
                'file_type': 'scoring_program',
                'creator': user_id
            },
            'reference_data': {
                'file_name': 'evaluation_data.zip',
                'file_path': '/app/src/apps/competitions/tests/files/evaluation_data.zip',
                'file_type': 'reference_data',
                'creator': user_id
            }
        },
        1: {
            'name': 'Final Phase Task',
            'description': 'Final phase',
            'created_by': user_id,
            'ingestion_only_during_scoring': False,
            'ingestion_program': {
                'file_name': 'ingestion_program.zip',
                'file_path': '/app/src/apps/competitions/tests/files/ingestion_program.zip',
                'file_type': 'ingestion_program',
                'creator': user_id
            },
            'input_data': {
                'file_name': 'evaluation_data.zip',
                'file_path': '/app/src/apps/competitions/tests/files/evaluation_data.zip',
                'file_type': 'input_data',
                'creator': user_id
            },
            'scoring_program': {
                'file_name': 'scoring_program.zip',
                'file_path': '/app/src/apps/competitions/tests/files/scoring_program.zip',
                'file_type': 'scoring_program',
                'creator': user_id
            },
            'reference_data': {
                'file_name': 'evaluation_data.zip',
                'file_path': '/app/src/apps/competitions/tests/files/evaluation_data.zip',
                'file_type': 'reference_data',
                'creator': user_id
            }
        }
    }
