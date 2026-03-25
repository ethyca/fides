import classNames from "classnames";
import { Alert, Flex } from "fidesui";
import NextLink from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ACTION_CTA } from "~/features/dashboard/constants";
import { useGetAgentBriefingQuery } from "~/features/dashboard/dashboard.slice";
import type { QuickAction } from "~/features/dashboard/types";
import { ActionSeverity } from "~/features/dashboard/types";

import styles from "./AgentBriefingBanner.module.scss";

const BRIEFING_DISMISSED_KEY = "dashboard_briefing_dismissed";

function getAlertType(
  quickActions: QuickAction[],
): "error" | "warning" | "info" {
  const has = (severity: ActionSeverity) =>
    quickActions.some((action) => action.severity === severity);
  if (has(ActionSeverity.CRITICAL) || has(ActionSeverity.HIGH)) {
    return "error";
  }
  if (has(ActionSeverity.MEDIUM)) {
    return "warning";
  }
  return "info";
}

export const AgentBriefingBanner = () => {
  const { data: briefing } = useGetAgentBriefingQuery();
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (sessionStorage.getItem(BRIEFING_DISMISSED_KEY) === "true") {
      setVisible(false);
    }
  }, []);

  const dismiss = useCallback(() => {
    setVisible(false);
    sessionStorage.setItem(BRIEFING_DISMISSED_KEY, "true");
  }, []);

  if (!briefing || !visible) {
    return null;
  }

  const { briefing: text, quick_actions: quickActions } = briefing;
  const alertType = getAlertType(quickActions);

  return (
    <Alert
      type={alertType}
      closable
      onClose={dismiss}
      message={
        <>
          {text}
          <Flex gap={16} className="mt-3">
            {quickActions.map((action) => {
              const cta = ACTION_CTA[action.action_type];
              if (!cta) {
                return null;
              }
              return (
                <NextLink
                  key={`${action.action_type}-${action.label}`}
                  href={cta.route(action.action_data)}
                  className={classNames(
                    styles.quickActionLink,
                    styles[alertType],
                  )}
                >
                  {action.label}
                </NextLink>
              );
            })}
          </Flex>
        </>
      }
      className={styles.alertSm}
    />
  );
};
