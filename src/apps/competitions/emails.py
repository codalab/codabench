from utils.email import codalab_send_mail


def get_organizer_emails(competition):
    return [competition.created_by.email] + [collab.email for collab in competition.collaborators.all()]


def send_participation_requested_emails(participant):
    context = {
        'participant': participant
    }
    # Notify Organizers
    codalab_send_mail(
        context_data=context,
        subject=f'{participant.user.username} applied to your competition',
        html_file="emails/participation/organizer/participation_requested.html",
        text_file="emails/participation/organizer/participation_requested.txt",
        to_email=get_organizer_emails(participant.competition)
    )

    # Notify User
    codalab_send_mail(
        context_data=context,
        subject=f'Application sent to {participant.competition.title}',
        html_file='emails/participation/participant/participation_requested.html',
        text_file='emails/participation/participant/participation_requested.txt',
        to_email=participant.user.email
    )


def send_participation_accepted_emails(participant):
    context = {
        'participant': participant
    }
    codalab_send_mail(
        context_data=context,
        subject=f'{participant.user.username} was accepted in to your competition',
        html_file="emails/participation/organizer/participation_accepted.html",
        text_file="emails/participation/organizer/participation_accepted.txt",
        to_email=get_organizer_emails(participant.competition)
    )
    # Notify User
    codalab_send_mail(
        context_data=context,
        subject=f'Participation status update for {participant.competition.title}',
        html_file='emails/participation/participant/participation_accepted.html',
        text_file='emails/participation/participant/participation_accepted.txt',
        to_email=participant.user.email
    )


def send_participation_denied_emails(participant):
    context = {
        'participant': participant
    }
    # Notify Organizers
    codalab_send_mail(
        context_data=context,
        subject=f'{participant.user.username} was denied from your competition',
        html_file="emails/participation/organizer/participation_denied.html",
        text_file="emails/participation/organizer/participation_denied.txt",
        to_email=get_organizer_emails(participant.competition)
    )
    # Notify User
    codalab_send_mail(
        context_data=context,
        subject=f'Participation status update for {participant.competition.title}',
        html_file='emails/participation/participant/participation_denied.html',
        text_file='emails/participation/participant/participation_denied.txt',
        to_email=participant.user.email
    )


def organizer_direct_emails():
    pass
