"""Notification services for Fides OSS.

This package provides two Celery tasks for DSR lifecycle notifications:

1. ``notify`` — event-driven task called directly when a DSR state change
   occurs.  This is the primary delivery path for immediate notifications.

2. ``sweep_notifications`` — scheduled task that runs on an interval to
   catch any notifications that were missed or failed on the primary path.

Both are no-ops until Fidesplus registers implementations.

Note: This is distinct from the ``messaging`` package, which is a
transport layer (email/SMS delivery via SES, Twilio, etc.).  This package
handles *when* and *why* to notify; ``messaging`` handles *how*.
"""
