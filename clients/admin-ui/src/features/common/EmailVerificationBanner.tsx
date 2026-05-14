import { Alert, Button, useMessage } from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";
import { useSelector } from "react-redux";

import {
  selectUser,
  useRequestEmailVerificationMutation,
} from "~/features/auth";
import { getErrorMessage } from "~/features/common/helpers";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { useGetEmailInviteStatusQuery } from "~/features/messaging/messaging.slice";
import { RTKErrorResult } from "~/types/errors/api";

const SNOOZE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days
const SNOOZE_KEY_PREFIX = "fides:email-verification-banner-snooze";

const buildSnoozeKey = (userId: string, emailAddress: string | null | undefined) =>
  `${SNOOZE_KEY_PREFIX}:${userId}:${emailAddress ?? "none"}`;

const isSnoozeActive = (key: string): boolean => {
  if (typeof window === "undefined") {
    return false;
  }
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) {
      return false;
    }
    const snoozedAt = Number.parseInt(raw, 10);
    if (Number.isNaN(snoozedAt)) {
      return false;
    }
    return Date.now() - snoozedAt < SNOOZE_TTL_MS;
  } catch {
    // localStorage can throw in private-mode/SSR — treat as no snooze.
    return false;
  }
};

const writeSnooze = (key: string) => {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(key, String(Date.now()));
  } catch {
    // No-op if storage isn't available.
  }
};

const EmailVerificationBanner = () => {
  const router = useRouter();
  const user = useSelector(selectUser);
  const { data: emailInviteStatus } = useGetEmailInviteStatusQuery(undefined, {
    skip: !user || Boolean(user.email_verified_at),
  });
  const [requestEmailVerification, { isLoading: isRequesting }] =
    useRequestEmailVerificationMutation();
  const message = useMessage();
  const [requestSent, setRequestSent] = useState(false);
  const [dismissed, setDismissed] = useState<boolean | null>(null);

  const snoozeKey = useMemo(
    () => (user ? buildSnoozeKey(user.id, user.email_address) : null),
    [user],
  );

  // Resolve snooze state on the client (after mount) to avoid SSR mismatches.
  useEffect(() => {
    if (!snoozeKey) {
      setDismissed(false);
      return;
    }
    setDismissed(isSnoozeActive(snoozeKey));
  }, [snoozeKey]);

  if (!user) {
    return null;
  }

  if (user.email_verified_at) {
    return null;
  }

  if (!emailInviteStatus?.enabled) {
    return null;
  }

  // Suppress for SSO-only users (mirrors fidesplus' service-level gating):
  // they can't use password recovery, so verification has no value for them.
  if (user.password_login_enabled === false) {
    return null;
  }

  // Haven't resolved snooze yet (first paint) or snooze is active.
  if (dismissed !== false) {
    return null;
  }

  const handleDismiss = () => {
    if (snoozeKey) {
      writeSnooze(snoozeKey);
    }
    setDismissed(true);
  };

  const hasEmail = Boolean(user.email_address);

  const handleSend = async () => {
    try {
      await requestEmailVerification().unwrap();
      setRequestSent(true);
    } catch (error) {
      const errorMsg = getErrorMessage(
        error as RTKErrorResult["error"],
        "Could not send verification email. Please try again.",
      );
      message.error(errorMsg);
    }
  };

  const handleAddEmail = () => {
    router.push(`${USER_MANAGEMENT_ROUTE}/profile/${user.id}#email_address`);
  };

  if (requestSent) {
    return (
      <Alert
        banner
        type="success"
        showIcon
        closable
        onClose={handleDismiss}
        message="Verification email sent — check your inbox for a link to verify your email address."
        data-testid="email-verification-banner-sent"
      />
    );
  }

  if (!hasEmail) {
    return (
      <Alert
        banner
        type="warning"
        showIcon
        closable
        onClose={handleDismiss}
        message="Add an email address to enable account recovery (self-service password reset)."
        action={
          <Button
            onClick={handleAddEmail}
            data-testid="email-verification-banner-add-email-btn"
          >
            Add email
          </Button>
        }
        data-testid="email-verification-banner-no-email"
      />
    );
  }

  return (
    <Alert
      banner
      type="warning"
      showIcon
      closable
      onClose={handleDismiss}
      message={`Please verify your email address (${user.email_address}) to enable account recovery.`}
      action={
        <Button
          onClick={handleSend}
          loading={isRequesting}
          data-testid="email-verification-banner-send-btn"
        >
          Send verification email
        </Button>
      }
      data-testid="email-verification-banner-unverified"
    />
  );
};

export default EmailVerificationBanner;
