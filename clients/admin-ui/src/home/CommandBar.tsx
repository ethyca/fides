import { antTheme, Flex, Statistic, Text } from "fidesui";
import { useCallback, useMemo } from "react";

import { useFlags } from "~/features/common/features";
import { ThemeModeSegmented } from "~/features/common/ThemeModeToggle";
import { BAND_CONFIG } from "~/features/dashboard/constants";
import {
  useGetDashboardPostureQuery,
  useGetPriorityActionsQuery,
  useGetSystemCoverageQuery,
} from "~/features/dashboard/dashboard.slice";
import {
  ActionSeverity,
  ActionStatus,
  ActionType,
  DiffDirection,
  PostureBand,
} from "~/features/dashboard/types";

import styles from "./CommandBar.module.scss";
import { useCountUp } from "./useCountUp";
import { openDashboardDrawer } from "./useDashboardDrawer";

function getDiffArrow(direction: DiffDirection): string {
  if (direction === DiffDirection.DOWN) {
    return "↓";
  }
  if (direction === DiffDirection.UP) {
    return "↑";
  }
  return "→";
}

export const CommandBar = () => {
  const { token } = antTheme.useToken();
  const {
    flags: { alphaDarkMode },
  } = useFlags();
  const { data: posture } = useGetDashboardPostureQuery();
  const { data: actions } = useGetPriorityActionsQuery();
  const { data: coverage } = useGetSystemCoverageQuery();

  const score = posture?.score ?? 0;
  const band = posture?.band ?? PostureBand.GOOD;
  const diffPercent = posture?.diff_percent ?? 0;
  const diffDirection = posture?.diff_direction ?? DiffDirection.UNCHANGED;

  const animatedScore = useCountUp(score);

  const scoreColorMap: Record<string, string> = {
    success: token.colorSuccess,
    info: token.colorInfo,
    caution: token.colorWarning,
    error: token.colorError,
  };

  const valueColorMap: Record<PostureBand, string | undefined> = {
    [PostureBand.EXCELLENT]: undefined,
    [PostureBand.GOOD]: undefined,
    [PostureBand.AT_RISK]: token.colorWarning,
    [PostureBand.CRITICAL]: token.colorError,
  };

  const bandConfig = BAND_CONFIG[band];
  const scoreColor = scoreColorMap[bandConfig.color];
  const valueColor = valueColorMap[band];

  const stats = useMemo(() => {
    const items = actions?.items ?? [];

    const pendingDsrs = items.filter(
      (a) =>
        a.type === ActionType.DSR_ACTION && a.status === ActionStatus.PENDING,
    ).length;

    const overdueDsrs = items.filter(
      (a) =>
        a.type === ActionType.DSR_ACTION &&
        a.severity === ActionSeverity.CRITICAL,
    ).length;

    const violations = items.filter(
      (a) => a.type === ActionType.POLICY_VIOLATION,
    ).length;

    return [
      { value: pendingDsrs, label: "DSRs pending" },
      { value: overdueDsrs, label: "overdue" },
      { value: coverage?.total_systems ?? 0, label: "systems" },
      { value: violations, label: "violations" },
    ];
  }, [actions?.items, coverage?.total_systems]);

  const openPostureDrawer = useCallback(() => {
    openDashboardDrawer({ type: "posture" });
  }, []);

  return (
    <Flex
      align="center"
      className="h-12 shrink-0 select-none px-10"
      // style={{ backgroundColor: token.colorBgLayout }}
    >
      <div className="mx-auto flex w-full max-w-[1600px] items-center">
        <Flex align="center" gap="large" className="flex-1">
          <Flex
            align="center"
            gap="small"
            role="button"
            tabIndex={0}
            className="cursor-pointer rounded-md px-2 py-1 transition-opacity hover:opacity-70"
            onClick={openPostureDrawer}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                openPostureDrawer();
              }
            }}
          >
            <Statistic
              value={animatedScore}
              // valueStyle={{ color: token.colorSuccess }}
              // size="lg"
              className={styles.scoreStatistic}
            />
            <Statistic
              value={diffPercent}
              prefix={getDiffArrow(diffDirection)}
              size="sm"
              className={styles.diffStatistic}
            />
          </Flex>

          <Text style={{ color: token.colorBorder }}>·</Text>

          {stats.map((stat, i) => (
            <Flex key={stat.label} align="center" gap={4}>
              {i > 0 && (
                <Text className="mr-2" style={{ color: token.colorBorder }}>
                  ·
                </Text>
              )}
              <Statistic
                value={stat.value}
                suffix={stat.label}
                valueStyle={valueColor ? { color: valueColor } : undefined}
                className={styles.barStatistic}
              />
            </Flex>
          ))}
        </Flex>
        {alphaDarkMode && <ThemeModeSegmented />}
      </div>
    </Flex>
  );
};
