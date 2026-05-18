"""Correspondence services for Fides OSS.

This package contains the Celery task skeleton and scheduler wiring for
polling an IMAP mailbox for DSR reply messages.  The actual polling
implementation is registered by Fidesplus.

Note: This is a domain feature (two-way communication with data subjects),
not a transport layer.  Correspondence *uses* the ``messaging`` package
to deliver emails but is separate from it — ``messaging`` handles how to
send; ``correspondence`` handles what to send, threading, and inbound
reply processing.
"""
