"""Send Web Push notifications for newly filed cards."""

import json

from pywebpush import WebPushException, webpush

from copium.config.settings import settings
from copium.storage.queries import delete_subscription, get_subscriptions

MAX_BODY_CHARS = 120


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


def notify_card(company: str, roast: str) -> int:
    """Push a new card to every registered device.

    Subscriptions expire when a browser is reinstalled or the user revokes
    permission. The push service reports that as 404 or 410, and the row is
    deleted rather than retried forever.

    Returns:
        How many devices were reached.
    """
    subscriptions = get_subscriptions()
    if not subscriptions:
        print("  [notify] no subscriptions registered")
        return 0

    payload = _payload(company, roast)
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
                print(f"  [notify] dropped expired subscription ({status})")
            else:
                print(f"  [notify] failed ({status}): {exc}")

    print(f"  [notify] delivered to {delivered}/{len(subscriptions)}")
    return delivered