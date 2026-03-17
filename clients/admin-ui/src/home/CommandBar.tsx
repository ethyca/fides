import { antTheme, Flex } from "fidesui";
import { useCallback, useMemo } from "react";

import { useFlags } from "~/features/common/features";
import { ThemeModeSegmented } from "~/features/common/ThemeModeToggle";
import { BAND_COLOR_TOKEN, BAND_CONFIG } from "~/features/dashboard/constants";
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

const BAND_VALUE_TOKEN: Record<
  PostureBand,
  "colorText" | "colorWarning" | "colorError"
> = {
  [PostureBand.EXCELLENT]: "colorText",
  [PostureBand.GOOD]: "colorText",
  [PostureBand.AT_RISK]: "colorWarning",
  [PostureBand.CRITICAL]: "colorError",
};

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

  const bandConfig = BAND_CONFIG[band];
  const valueColor = token[BAND_VALUE_TOKEN[band]];

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

  const scoreColor = token[BAND_COLOR_TOKEN[bandConfig.color]];

  const openPostureDrawer = useCallback(() => {
    openDashboardDrawer({ type: "posture" });
  }, []);

  return (
    <Flex
      align="center"
      className="h-12 select-none px-10"
      style={{ backgroundColor: token.colorBgLayout }}
    >
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
          <span className="text-lg font-bold" style={{ color: scoreColor }}>
            {animatedScore}
          </span>
          <span className="text-xs" style={{ color: token.colorTextSecondary }}>
            {getDiffArrow(diffDirection)} {diffPercent}
          </span>
        </Flex>

        <span style={{ color: token.colorBorder }}>·</span>

        {stats.map((stat, i) => (
          <Flex key={stat.label} align="center" gap={4}>
            {i > 0 && (
              <span className="mr-2" style={{ color: token.colorBorder }}>
                ·
              </span>
            )}
            <span
              className="text-sm font-semibold"
              style={{ color: valueColor }}
            >
              {stat.value}
            </span>
            <span
              className="text-sm"
              style={{ color: token.colorTextSecondary }}
            >
              {stat.label}
            </span>
          </Flex>
        ))}
      </Flex>
      {alphaDarkMode && <ThemeModeSegmented />}
    </Flex>
  );
};
