import { Button, Flex, Icons, SparkleIcon, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useCallback, useState } from "react";

import { SEVERITY_COLORS } from "../constants";
import type { MockSystem, SystemRisk } from "../types";

interface SystemBriefingBannerProps {
  system: MockSystem;
  onNavigate?: (tab: string) => void;
}

function buildRichBriefing(system: MockSystem): string {
  const parts: string[] = [];

  parts.push(
    `${system.name} is a ${system.system_type.toLowerCase()} operated by the ${system.department} team as a ${system.responsibility.toLowerCase()}.`,
  );

  if (system.purposes.length > 0) {
    parts.push(
      `It processes data for ${system.purposes.map((p) => p.name.toLowerCase()).join(", ")}.`,
    );
  }

  if (system.roles.length > 0) {
    const roleDesc = system.roles
      .map((r) =>
        r === "producer"
          ? "produces data for downstream systems"
          : "consumes data from upstream sources",
      )
      .join(" and ");
    parts.push(`This system ${roleDesc}.`);
  }

  if (system.annotation_percent >= 80) {
    parts.push(
      `Annotation coverage is strong at ${system.annotation_percent}%.`,
    );
  } else if (system.annotation_percent >= 50) {
    parts.push(
      `Annotation coverage is at ${system.annotation_percent}% — there's room to improve.`,
    );
  } else {
    parts.push(
      `Annotation coverage is low at ${system.annotation_percent}% and needs attention.`,
    );
  }

  return parts.join(" ");
}

const HREF_TO_TAB: Record<string, string> = {
  "#datasets": "datasets",
  "#integrations": "overview",
  "#assets": "assets",
  "#information": "overview",
  "#config": "overview",
};

function getTabForRisk(risk: SystemRisk): string {
  return HREF_TO_TAB[risk.resolveHref] ?? "overview";
}

const SystemBriefingBanner = ({
  system,
  onNavigate,
}: SystemBriefingBannerProps) => {
  const briefing = system.agentBriefing ?? buildRichBriefing(system);
  const allRisks = system.risks;
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const dismiss = useCallback((id: string) => {
    setDismissed((prev) => new Set(prev).add(id));
  }, []);

  const visibleRisks = allRisks.filter((r) => !dismissed.has(r.id));

  return (
    <div
      className="mb-6 rounded-lg px-5 py-4"
      style={{ backgroundColor: palette.FIDESUI_BG_DEFAULT }}
    >
      <Flex gap={12} align="flex-start" className="min-w-0">
        <SparkleIcon size={16} className="mt-1 shrink-0" />
        <Flex vertical gap={6} className="min-w-0 flex-1">
          <Text className="text-sm leading-relaxed">{briefing}</Text>

          {visibleRisks.length > 0 && (
            <Flex vertical gap={4}>
              <Flex justify="space-between" align="center">
                <Text strong className="text-[10px] uppercase tracking-wider">
                  Risks
                </Text>
                <Button
                  type="text"
                  size="small"
                  className="!px-0 !text-[10px]"
                  style={{ color: palette.FIDESUI_NEUTRAL_500 }}
                  onClick={() => {
                    visibleRisks.forEach((r) => dismiss(r.id));
                  }}
                >
                  Dismiss all
                </Button>
              </Flex>
              {visibleRisks.map((risk) => (
                <Flex key={risk.id} align="center" gap={6}>
                  <div
                    className="size-2 shrink-0 rounded-full"
                    style={{
                      backgroundColor: SEVERITY_COLORS[risk.severity],
                    }}
                  />
                  <Text className="min-w-0 flex-1 text-xs">{risk.title}</Text>
                  <Button
                    type="text"
                    size="small"
                    className="!px-0 !text-xs"
                    style={{ color: palette.FIDESUI_MINOS }}
                    onClick={() => onNavigate?.(getTabForRisk(risk))}
                  >
                    View
                  </Button>
                  <span
                    role="button"
                    aria-label={`Dismiss ${risk.title}`}
                    tabIndex={0}
                    className="shrink-0 cursor-pointer"
                    onClick={() => dismiss(risk.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        dismiss(risk.id);
                      }
                    }}
                  >
                    <Icons.Close
                      size={12}
                      style={{ color: palette.FIDESUI_NEUTRAL_500 }}
                    />
                  </span>
                </Flex>
              ))}
            </Flex>
          )}

          {visibleRisks.length === 0 && allRisks.length === 0 && (
            <Tag bordered={false} color="success" className="!text-[10px]">
              No risks — this system is in good health
            </Tag>
          )}
        </Flex>
      </Flex>
    </div>
  );
};

export default SystemBriefingBanner;
