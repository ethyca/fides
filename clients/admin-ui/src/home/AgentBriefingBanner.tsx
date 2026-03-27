import { Alert, Flex, SparkleIcon } from "fidesui";
import NextLink from "next/link";
import { useCallback, useState } from "react";

import { ACTION_CTA } from "~/features/dashboard/constants";
import { useGetAgentBriefingQuery } from "~/features/dashboard/dashboard.slice";

import styles from "./AgentBriefingBanner.module.scss";

export const AgentBriefingBanner = () => {
  const { data: briefing } = useGetAgentBriefingQuery();
  const [visible, setVisible] = useState(true);

  const dismiss = useCallback(() => {
    setVisible(false);
  }, []);

  if (!briefing || !visible) {
    return null;
  }

  const { briefing: text, quick_actions: quickActions } = briefing;

  return (
    <Alert
      type="info"
      showIcon
      icon={<SparkleIcon size={14} />}
      closable
      onClose={dismiss}
      message={
        <>
          {text}
          <Flex gap={16} className="mt-3" wrap="wrap">
            {quickActions.map((action) => {
              const cta = ACTION_CTA[action.action_type];
              if (!cta) {
                return null;
              }
              return (
                <NextLink
                  key={`${action.action_type}-${action.label}`}
                  href={cta.route(action.action_data)}
                  className={styles.quickActionLink}
                >
                  {action.label} &rarr;
                </NextLink>
              );
            })}
          </Flex>
        </>
      }
      className={styles.astralisAlert}
    />
  );
};
