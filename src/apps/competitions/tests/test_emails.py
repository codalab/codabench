from types import SimpleNamespace
from unittest import mock

from competitions.emails import send_participation_requested_emails


def test_participation_request_uses_each_recipient_as_email_user():
    participant_user = SimpleNamespace(
        username='participant', email='participant@example.com', is_deleted=False
    )
    organizers = [
        SimpleNamespace(username='owner', email='owner@example.com', is_deleted=False),
        SimpleNamespace(username='collaborator', email='collaborator@example.com', is_deleted=False),
        SimpleNamespace(username='deleted', email='deleted@example.com', is_deleted=True),
    ]
    participant = SimpleNamespace(
        user=participant_user,
        competition=SimpleNamespace(title='Competition', all_organizers=organizers),
    )

    with mock.patch('competitions.emails.codalab_send_mail') as send_mail:
        send_participation_requested_emails(participant)

    assert [call.kwargs['to_email'] for call in send_mail.call_args_list] == [
        'owner@example.com',
        'collaborator@example.com',
        'participant@example.com',
    ]
    assert [call.kwargs['context_data']['user'] for call in send_mail.call_args_list] == [
        organizers[0],
        organizers[1],
        participant_user,
    ]
