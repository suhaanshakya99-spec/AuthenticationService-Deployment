from brevo import Brevo
from brevo.transactional_emails import (SendTransacEmailRequestSender, SendTransacEmailRequestToItem)
from core.config import settings

"""
Replacement for the old core/celery.py tasks.

These used to be Celery tasks dispatched via `.delay(...)` onto a
Redis-backed broker/worker. Since Celery + Redis have been removed,
these are now plain functions meant to be scheduled with FastAPI's
BackgroundTasks (`background_tasks.add_task(fn, ...)`), which runs
them in a threadpool after the response is returned -- no separate
worker process or broker required.

Trade-off: there's no automatic retry-on-failure or persistence
across restarts like Celery gave us. If a background task fails
(e.g. the email provider is down), it's simply logged and dropped.
That's an acceptable trade for a local/single-instance setup; a
production deployment that needs guaranteed delivery should bring
back a real task queue.
"""


def send_developer_verification_mail(verification_token: str, receiver_email: str):
    api = settings.BREVO_API
    sender = settings.SENDER_EMAIL

    client = Brevo(api_key=api)

    try:
        result = client.transactional_emails.send_transac_email(
            subject="Verification Email",
            sender=SendTransacEmailRequestSender(name="AuthSaas", email=sender),
            to=[SendTransacEmailRequestToItem(email=receiver_email)],
            html_content=f"""
            <html>
                <body>
                    <h2>Verify your email</h2>

                    <p>
                        Thanks for signing up!
                        Click the button below to verify your email.
                    </p>

                    <a href="{verification_token}">
                        Verify Email
                    </a>

                    <p>This link expires in 30 minutes.</p>
                </body>
            </html>
            """
        )
        return result.message_id
    except Exception as e:
        print(f"Failed to send developer verification email to {receiver_email}: {e}")
        return None


def send_user_verification_mail(receiver_email: str, verification_token: str):
    api = settings.BREVO_API
    sender = settings.SENDER_EMAIL

    brevo = Brevo(api_key=api)

    try:
        response = brevo.transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(name="Auth", email=sender),
            subject="Verification",
            to=[SendTransacEmailRequestToItem(email=receiver_email)],
            html_content=f"""
                    <html>
                        <body>
                            <h2>Verify your email</h2>

                            <p>
                                Thanks for signing up!
                                Click the button below to verify your email.
                            </p>

                            <a href="{verification_token}">
                                Verify Email
                            </a>

                            <p>This link expires in 30 minutes.</p>
                        </body>
                    </html>
                    """
        )
        return response.message_id
    except Exception as e:
        print(f"Failed to send end-user verification email to {receiver_email}: {e}")
        return None
