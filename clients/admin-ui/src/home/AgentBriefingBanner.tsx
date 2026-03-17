import classNames from "classnames";
import { Alert, Flex } from "fidesui";
import NextLink from "next/link";

import { ACTION_CTA } from "~/features/dashboard/constants";
import type { QuickAction } from "~/features/dashboard/types";
import { ActionSeverity } from "~/features/dashboard/types";

import styles from "./AgentBriefingBanner.module.scss";

interface AgentBriefingBannerProps {
  briefing: string;
  quickActions: QuickAction[];
  onClose: () => void;
}

// TODO Refactor this
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

export const AgentBriefingBanner = ({
  briefing,
  quickActions,
  onClose,
}: AgentBriefingBannerProps) => {
  const alertType = getAlertType(quickActions);

  return (
    <Alert
      type={alertType}
      closable
      onClose={onClose}
      message={
        <>
          {briefing}
          <Flex gap={16} className="mt-3">
            {quickActions.map((action) => {
              const cta = ACTION_CTA[action.action_type];
              return (
                <NextLink
                  key={action.label}
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
