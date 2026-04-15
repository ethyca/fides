import {
  Alert,
  Button,
  ConfigProvider,
  Flex,
  SparkleIcon,
  useThemeMode,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import NextLink from "next/link";
import { useMemo } from "react";

import { useFlags } from "~/features/common/features";
import { ACTION_CTA } from "~/features/dashboard/constants";
import { useGetAgentBriefingQuery } from "~/features/dashboard/dashboard.slice";
import { ActionSeverity } from "~/features/dashboard/types";

import styles from "./AgentBriefingBanner.module.scss";

const SEVERITY_STYLE: Record<ActionSeverity, string> = {
  [ActionSeverity.CRITICAL]: styles.error,
  [ActionSeverity.HIGH]: styles.error,
  [ActionSeverity.MEDIUM]: styles.warning,
  [ActionSeverity.LOW]: styles.info,
};

export const AgentBriefingBanner = () => {
  const {
    flags: { alphaDashboardAgentBriefingActions },
  } = useFlags();
  const { data: briefing } = useGetAgentBriefingQuery();
  const { resolvedMode } = useThemeMode();

  const alertTheme = useMemo(
    () => ({
      components: {
        Alert: {
          colorInfoBg:
            resolvedMode === "dark"
              ? palette.FIDESUI_MINOS
              : palette.FIDESUI_LIMESTONE,
          colorInfoBorder:
            resolvedMode === "dark"
              ? palette.FIDESUI_MINOS
              : palette.FIDESUI_LIMESTONE,
        },
      },
    }),
    [resolvedMode],
  );

  if (!briefing) {
    return null;
  }

  const { briefing: text, quick_actions: quickActions } = briefing;

  return (
    <ConfigProvider theme={alertTheme}>
      <Alert
        type="info"
        showIcon
        icon={<SparkleIcon size={14} />}
        closable
        message={
          <>
            {text}
            {alphaDashboardAgentBriefingActions && (
              <Flex gap={16} className="mt-3">
                {quickActions.map((action) => {
                  const cta = ACTION_CTA[action.action_type];
                  if (!cta) {
                    return null;
                  }
                  const severityClass =
                    SEVERITY_STYLE[action.severity] ?? styles.info;
                  return (
                    <NextLink
                      key={`${action.action_type}-${action.label}`}
                      href={cta.route(action.action_data)}
                      className={styles.quickActionTile}
                    >
                      <Button
                        size="small"
                        className={`${styles.quickActionButton} ${severityClass}`}
                      >
                        {action.label}
                      </Button>
                    </NextLink>
                  );
                })}
              </Flex>
            )}
          </>
        }
        className={styles.alertSm}
      />
    </ConfigProvider>
  );
};
