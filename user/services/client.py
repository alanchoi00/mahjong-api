from core.exceptions import catch_and_reraise
from user.exceptions import ClientNotFound
from user.models import Client


def identify_client(*, install_id: str, label: str = '') -> Client:
    """
    Get or create a client by install_id and update last_seen_at.

    If the client exists, updates last_seen_at.
    If the client doesn't exist, creates a new one.
    """
    client, created = Client.objects.get_or_create(
        install_id=install_id,
        defaults={'label': label},
    )

    if not created:
        client.touch()
        if label and label != client.label:
            client.label = label
            client.save(update_fields=['label'])

    return client


def get_client(*, install_id: str) -> Client:
    """
    Get a client by install_id.

    Raises Client.DoesNotExist if not found.
    """
    with catch_and_reraise(
        Client.DoesNotExist,
        ClientNotFound,
        f"Client with install_id '{install_id}' not found",
    ):
        return Client.objects.get(install_id=install_id)


def delete_client(*, install_id: str) -> None:
    """
    Delete a client by install_id.

    Raises Client.DoesNotExist if not found.
    """
    with catch_and_reraise(
        Client.DoesNotExist,
        ClientNotFound,
        f"Client with install_id '{install_id}' not found",
    ):
        client = Client.objects.get(install_id=install_id)
        client.delete()
