from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from repository.utils.general_utils import get_observation_list


def send_confirmation_email(obs_ids: list[int], email_address: str | bool):
    """
    Sends a confirmation email with observation IDs for reference.

    This function checks if the email backend is in the settings file and returns if
    not. It then creates a text body with the observation list and sends an email with
    the observation IDs.

    Args:
        obs_ids (list[int]): A list of observation IDs.
        email_address (str): The email address to send the confirmation to.

    Returns:
        None
    """
    # check if email backend is in settings file and return if not
    #
    # if not hasattr(settings, "ANYMAIL"):
    #    return
    text_body = get_observation_list(False, obs_ids)

    msg = EmailMultiAlternatives(
        "SCORE Observation Upload Confirmation",
        "SCORE Observation Upload Confirmation \n\n Thank you for submitting your \
            observations. Your observations have been successfully uploaded to the \
                SCORE database.  The observation ID(s) are: \n\n"
        + text_body,
        settings.EMAIL_HOST_USER,
        [email_address],
    )

    email_body = """
    <html>
        <h2>SCORE Observation Upload Confirmation</h2>
        <p>
            Thank you for submitting your observations. Your observations have
            been successfully uploaded to the SCORE database.
            The observation ID(s) are:
        </p>
    """
    email_body += get_observation_list(True, obs_ids)
    email_body += "</html>"
    msg.attach_alternative(email_body, "text/html")
    msg.send()


def send_data_change_email(contact_email: str, obs_ids: str, reason: str):
    """
    Sends a data change email with observation IDs, reason for change, and contact email

    Args:
        contact_email (str): The contact email from the form.
        obs_ids (str): The observation IDs from the form.
        reason (str): The reason for data change/deletion from the form.
        email_address (str): The email address to send the data change email to.

    Returns:
        None
    """
    text_body = f"""
    Contact Email: {contact_email}
    Observation IDs: {obs_ids}
    Reason for Data Change/Deletion: {reason}
    """

    msg = EmailMultiAlternatives(
        "SCORE Data Change Request",
        text_body,
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER],
    )

    email_body = f"""
    <html>
    <h2>SCORE Data Change Request</h2>
    <p>Contact Email: {contact_email}</p>
    <p>Observation IDs: {obs_ids}</p>
    <p>Reason for Data Change/Deletion: {reason}</p>
    </html>
    """
    msg.attach_alternative(email_body, "text/html")
    msg.send()
