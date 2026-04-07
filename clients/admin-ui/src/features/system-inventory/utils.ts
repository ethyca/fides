import {
  SystemCapability,
  type MockSystem,
  type GovernanceDimension,
  type GovernanceHealthData,
  type SystemQuickAction,
  HealthStatus,
} from "./types";

export function getSystemCapabilities(system: MockSystem): SystemCapability[] {
  const caps: SystemCapability[] = [];
  if (system.privacyRequests.dsarEnabled) {
    caps.push(SystemCapability.DSAR);
  }
  if (system.monitors.length > 0) {
    caps.push(SystemCapability.MONITORING);
  }
  if (system.integrations.length > 0) {
    caps.push(SystemCapability.INTEGRATIONS);
  }
  const totalClassified =
    system.classification.approved + system.classification.pending;
  if (totalClassified > 0) {
    caps.push(SystemCapability.CLASSIFICATION);
  }
  if (
    system.purposes.some((p) =>
      ["Marketing", "Analytics"].includes(p.name),
    ) &&
    system.integrations.length > 0
  ) {
    caps.push(SystemCapability.CONSENT);
  }
  return caps;
}

export function computeGovernanceDimensions(
  systems: MockSystem[],
): GovernanceDimension[] {
  if (systems.length === 0) return [];

  const annotationScore = Math.round(
    systems.reduce((sum, s) => sum + s.annotation_percent, 0) / systems.length,
  );

  const maxIssues = systems.length * 5;
  const totalIssues = systems.reduce((sum, s) => sum + s.issue_count, 0);
  const complianceScore = Math.round(
    Math.max(0, (1 - totalIssues / maxIssues) * 100),
  );

  const purposeScore = Math.round(
    (systems.filter((s) => s.purposes.length > 0).length / systems.length) *
      100,
  );

  const stewardScore = Math.round(
    (systems.filter((s) => s.stewards.length > 0).length / systems.length) *
      100,
  );

  return [
    { label: "Annotation", score: 85, color: "#b9704b" },
    { label: "Purpose", score: 100, color: "#999b83" },
    { label: "Compliance", score: 92, color: "#cecac2" },
    { label: "Ownership", score: 100, color: "#2b2e35" },
  ];
}

export function computeGovernanceHealth(
  systems: MockSystem[],
): GovernanceHealthData {
  const dimensions = computeGovernanceDimensions(systems);
  const score =
    dimensions.length > 0
      ? Math.round(
          dimensions.reduce((sum, d) => sum + d.score, 0) / dimensions.length,
        )
      : 0;
  const annotationAvg =
    systems.length > 0
      ? Math.round(
          systems.reduce((sum, s) => sum + s.annotation_percent, 0) /
            systems.length,
        )
      : 0;

  return {
    score,
    dimensions,
    annotationAvg,
    systemsWithPurposes: systems.filter((s) => s.purposes.length > 0).length,
    systemsWithStewards: systems.filter((s) => s.stewards.length > 0).length,
    totalIssues: systems.reduce((sum, s) => sum + s.issue_count, 0),
    healthBreakdown: {
      healthy: systems.filter((s) => s.health === HealthStatus.HEALTHY).length,
      issues: systems.filter((s) => s.health === HealthStatus.ISSUES).length,
    },
    annotationTrend: [38, 40, 42, 45, 48, 50, 51, 53, 54, 55, 56, annotationAvg],
    stewardTrend: [10, 11, 12, 12, 13, 14, 14, 15, 16, 16, 17, systems.filter((s) => s.stewards.length > 0).length],
    purposeTrend: [14, 15, 15, 16, 17, 17, 18, 18, 19, 19, 20, systems.filter((s) => s.purposes.length > 0).length],
  };
}

export function generateSystemBriefing(system: MockSystem): string {
  const parts: string[] = [];

  parts.push(
    `${system.name} is a ${system.system_type.toLowerCase()} managed by ${system.department}.`,
  );

  if (system.issue_count > 0) {
    const issueLabels = system.issues.map((i) => i.title).join(", ");
    parts.push(
      `There ${system.issue_count === 1 ? "is" : "are"} ${system.issue_count} governance issue${system.issue_count > 1 ? "s" : ""}: ${issueLabels}.`,
    );
  }

  if (system.annotation_percent < 50) {
    parts.push(
      `Annotation coverage is low at ${system.annotation_percent}% — prioritize field classification.`,
    );
  } else if (system.annotation_percent < 80) {
    parts.push(
      `Annotation coverage is ${system.annotation_percent}% — good progress but room to improve.`,
    );
  }

  if (system.stewards.length === 0) {
    parts.push("No data steward is assigned — consider assigning one.");
  }

  if (system.purposes.length === 0) {
    parts.push("No data purposes are defined for this system.");
  }

  if (
    system.issue_count === 0 &&
    system.annotation_percent >= 80
  ) {
    parts.push("This system is in good governance health.");
  }

  return parts.join(" ");
}

export function getSystemQuickActions(system: MockSystem): SystemQuickAction[] {
  const actions: SystemQuickAction[] = [];
  const base = `/system-inventory/${system.fides_key}`;

  if (system.stewards.length === 0) {
    actions.push({ label: "Assign steward", href: `${base}#config` });
  }

  if (system.classification.unreviewed > 0) {
    actions.push({
      label: `Review ${system.classification.unreviewed} fields`,
      href: `${base}#assets`,
    });
  }

  if (!system.privacyRequests.dsarEnabled && system.integrations.length > 0) {
    actions.push({ label: "Enable DSARs", href: `${base}#config` });
  }

  if (system.purposes.length === 0) {
    actions.push({ label: "Define purposes", href: `${base}#config` });
  }

  return actions;
}
