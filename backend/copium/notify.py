"""Send Web Push notifications for newly filed cards."""

import json
import re

from pywebpush import WebPushException, webpush

from copium.config.settings import settings
from copium.log import step, detail
from copium.storage.queries import delete_subscription, get_subscriptions

MAX_BODY_CHARS = 120

ACTIONABLE = {"advancement", "offer"}

TITLES = {
    "advancement": "They want to talk",
    "offer": "An offer",
}


def _sender_name(sender: str) -> str:
    """'Stripe Recruiting <no-reply@ashbyhq.com>' -> 'Stripe Recruiting'."""
    match = re.match(r'\s*"?([^"<]+?)"?\s*<', sender)
    return (match.group(1) if match else sender).strip()


def _payload(company: str, roast: str) -> str:
    """Build the notification body the service worker will render."""
    body = roast if len(roast) <= MAX_BODY_CHARS else f"{roast[:MAX_BODY_CHARS - 1]}…"

    return json.dumps(
        {
            "title": company,
            "body": body,
            "url": "/",
            # Same tag means a second push replaces the first rather than
            # stacking, so duplicate deliveries never produce two banners.
            "tag": "copium-card",
        }
    )

def _send(payload: str) -> int:
    """Deliver one payload to every registered device.

    Subscriptions expire when a browser is reinstalled or permission is
    revoked. The push service reports that as 404 or 410, and the row is
    deleted rather than retried forever.
    """
    subscriptions = get_subscriptions()
    if not subscriptions:
        step("notify", "no subscriptions")
        return 0

    delivered = 0

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription["endpoint"],
                    "keys": {
                        "p256dh": subscription["p256dh"],
                        "auth": subscription["auth"],
                    },
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
            )
            delivered += 1

        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None)

            if status in (404, 410):
                delete_subscription(subscription["endpoint"])
                step("notify", f"dropped expired subscription ({status})")
            else:
                step("notify", f"failed ({status})")

    step("notify", f"delivered {delivered}/{len(subscriptions)}")
    return delivered


def notify_card(company: str, roast: str) -> int:
    """Push a new roast card to every registered device."""
    return _send(_payload(company, roast))


def notify_action(category: str, email: dict, message_id: str) -> int:
    """Push a time-sensitive non-rejection, linking straight to Gmail.

    These get no card and no roast. The point is speed: an interview invite
    should reach the phone and open the real email in one tap.
    """
    sender = _sender_name(email.get("sender", ""))
    subject = email.get("subject", "")

    payload = json.dumps(
        {
            "title": TITLES.get(category, "Something arrived"),
            "body": f"{sender} · {subject}" if sender else subject,
            "url": "/",
            # Per-message tag so two invites do not collapse into one banner.
            "tag": f"copium-{message_id}",
        }
    )

    return _send(payload)