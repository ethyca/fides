import { Button, Flex, SparkleIcon, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import NextLink from "next/link";
import { useCallback, useEffect, useState } from "react";

import { type MockSystem } from "../types";

interface SystemBriefingBannerProps {
  system: MockSystem;
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

interface Issue {
  label: string;
  action: string;
  href: string;
  severity: "error" | "warning";
}

function getIssues(system: MockSystem): Issue[] {
  const issues: Issue[] = [];
  const base = `/system-inventory/${system.fides_key}`;

  if (system.stewards.length === 0) {
    issues.push({
      label: "No steward assigned",
      action: "Assign steward",
      href: `${base}#config`,
      severity: "warning",
    });
  }
  const needsReview =
    system.classification.unreviewed + system.classification.pending;
  if (needsReview > 0) {
    issues.push({
      label: `${needsReview.toLocaleString()} fields need review`,
      action: "Review fields",
      href: `${base}#assets`,
      severity: "warning",
    });
  }
  if (system.purposes.length === 0) {
    issues.push({
      label: "No purposes defined",
      action: "Define purposes",
      href: `${base}#config`,
      severity: "warning",
    });
  }
  if (!system.privacyRequests.dsarEnabled && system.integrations.length > 0) {
    issues.push({
      label: "DSAR not enabled",
      action: "Enable DSARs",
      href: `${base}#config`,
      severity: "warning",
    });
  }
  system.issues.forEach((issue) => {
    issues.push({
      label: issue.title,
      action: "Resolve",
      href: issue.resolveHref,
      severity: issue.severity === "error" ? "error" : "warning",
    });
  });
  return issues;
}

const SystemBriefingBanner = ({ system }: SystemBriefingBannerProps) => {
  const storageKey = `system_briefing_dismissed_${system.fides_key}`;
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (sessionStorage.getItem(storageKey) === "true") {
      setVisible(false);
    }
  }, [storageKey]);

  const dismiss = useCallback(() => {
    setVisible(false);
    sessionStorage.setItem(storageKey, "true");
  }, [storageKey]);

  if (!visible) {
    return null;
  }

  const briefing = system.agentBriefing ?? buildRichBriefing(system);
  const issues = getIssues(system);

  return (
    <div
      className="mb-6 rounded-lg px-5 py-4"
      style={{ backgroundColor: palette.FIDESUI_BG_DEFAULT }}
    >
      <Flex justify="space-between" align="flex-start">
        <Flex gap={12} align="flex-start" className="min-w-0 flex-1">
          <SparkleIcon size={16} className="mt-1 shrink-0" />
          <Flex vertical gap={8}>
            <Text className="text-sm leading-relaxed">{briefing}</Text>

            {issues.length > 0 && (
              <Flex vertical gap={6}>
                <Text strong className="text-[10px] uppercase tracking-wider">
                  Needs attention
                </Text>
                <Flex gap={8} wrap>
                  {issues.map((issue) => (
                    <Flex key={issue.label} align="center" gap={6}>
                      <Tag
                        bordered={false}
                        color="error"
                        className="!text-[10px]"
                      >
                        {issue.label}
                      </Tag>
                      <NextLink href={issue.href}>
                        <Button
                          type="text"
                          size="small"
                          className="!px-0 !text-[11px] !font-medium"
                          style={{ color: palette.FIDESUI_MINOS }}
                        >
                          {issue.action} &rarr;
                        </Button>
                      </NextLink>
                    </Flex>
                  ))}
                </Flex>
              </Flex>
            )}

            {issues.length === 0 && (
              <Tag bordered={false} color="success" className="!text-[10px]">
                No issues — this system is in good health
              </Tag>
            )}
          </Flex>
        </Flex>
        <Button
          type="text"
          size="small"
          className="shrink-0 pl-4 text-xs"
          onClick={dismiss}
        >
          Dismiss
        </Button>
      </Flex>
    </div>
  );
};

export default SystemBriefingBanner;
