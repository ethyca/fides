import { PILLAR_CONFIG } from "./constants";
import {
  type GovernanceDimension,
  type GovernanceHealthData,
  HealthStatus,
  type MockSystem,
  PillarKey,
  RiskFreshness,
  SystemCapability,
  type SystemQuickAction,
  type SystemRisk,
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
  return caps;
}

function buildDimension(
  key: PillarKey,
  numerator: number,
  denominator: number,
  score: number,
): GovernanceDimension {
  const { label, color } = PILLAR_CONFIG[key];
  return { key, label, score, numerator, denominator, color };
}

function safePercent(num: number, denom: number): number {
  return denom === 0 ? 0 : Math.round((num / denom) * 100);
}

// --- Per-system risk check: count how many governance checks flag a risk ---

function countSystemRiskChecks(system: MockSystem): {
  flagged: number;
  total: number;
} {
  let flagged = 0;
  let total = 0;

  // Standard governance checks
  total += 1; // steward assigned
  if (system.stewards.length === 0) {
    flagged += 1;
  }
  total += 1; // purpose defined
  if (system.purposes.length === 0) {
    flagged += 1;
  }
  total += 1; // integration linked
  if (system.integrations.length === 0) {
    flagged += 1;
  }
  total += 1; // DSAR enabled
  if (!system.privacyRequests.dsarEnabled) {
    flagged += 1;
  }
  total += 1; // annotation ≥ 50%
  if (system.annotation_percent < 50) {
    flagged += 1;
  }
  total += 1; // monitors configured
  if (system.monitors.length === 0) {
    flagged += 1;
  }

  // Each explicit risk from mock data
  total += system.risks.length;
  flagged += system.risks.length;

  return { flagged, total };
}

export function computeRiskScore(system: MockSystem): number {
  const { flagged, total } = countSystemRiskChecks(system);
  if (total === 0) {
    return 100;
  }
  return Math.round(100 - (flagged / total) * 100);
}

export function computeGovernanceDimensions(
  systems: MockSystem[],
): GovernanceDimension[] {
  if (systems.length === 0) {
    return [
      buildDimension(PillarKey.COVERAGE, 0, 0, 0),
      buildDimension(PillarKey.CLASSIFICATION, 0, 0, 0),
      buildDimension(PillarKey.RISK, 0, 0, 100),
    ];
  }

  // Coverage: systems meeting bar (annotation ≥ 50% + has purpose + has steward)
  const coveredSystems = systems.filter(
    (s) =>
      s.annotation_percent >= 50 &&
      s.purposes.length > 0 &&
      s.stewards.length > 0,
  ).length;

  // Classification: approved / total fields
  const classApproved = systems.reduce(
    (sum, s) => sum + s.classification.approved,
    0,
  );
  const classTotal = systems.reduce(
    (sum, s) =>
      sum +
      s.classification.approved +
      s.classification.pending +
      s.classification.unreviewed,
    0,
  );

  // Risks: aggregate flagged / total checks
  let totalFlagged = 0;
  let totalChecks = 0;
  systems.forEach((s) => {
    const { flagged, total } = countSystemRiskChecks(s);
    totalFlagged += flagged;
    totalChecks += total;
  });

  return [
    buildDimension(
      PillarKey.COVERAGE,
      coveredSystems,
      systems.length,
      safePercent(coveredSystems, systems.length),
    ),
    buildDimension(
      PillarKey.CLASSIFICATION,
      classApproved,
      classTotal,
      safePercent(classApproved, classTotal),
    ),
    buildDimension(
      PillarKey.RISK,
      totalFlagged,
      totalChecks,
      totalChecks === 0
        ? 100
        : Math.round(100 - (totalFlagged / totalChecks) * 100),
    ),
  ];
}

export function computeSystemDimensions(
  system: MockSystem,
): GovernanceDimension[] {
  // Coverage: 3 sub-checks
  const covChecks = [
    system.annotation_percent >= 50,
    system.purposes.length > 0,
    system.stewards.length > 0,
  ];
  const covPassing = covChecks.filter(Boolean).length;

  // Classification
  const { approved, pending, unreviewed } = system.classification;
  const classTotal = approved + pending + unreviewed;

  // Risks
  const { flagged, total: riskTotal } = countSystemRiskChecks(system);

  return [
    buildDimension(
      PillarKey.COVERAGE,
      covPassing,
      3,
      safePercent(covPassing, 3),
    ),
    buildDimension(
      PillarKey.CLASSIFICATION,
      approved,
      classTotal,
      safePercent(approved, classTotal),
    ),
    buildDimension(
      PillarKey.RISK,
      flagged,
      riskTotal,
      riskTotal === 0 ? 100 : Math.round(100 - (flagged / riskTotal) * 100),
    ),
  ];
}

// Target pillar scores for the root dashboard demo. These ensure the overall
// health score is 75 to match the "health over time" trend endpoint.
const ROOT_PILLAR_OVERRIDES: Record<PillarKey, number> = {
  [PillarKey.COVERAGE]: 70,
  [PillarKey.CLASSIFICATION]: 65,
  [PillarKey.RISK]: 90,
};

export function computeGovernanceHealth(
  systems: MockSystem[],
): GovernanceHealthData {
  const rawDimensions = computeGovernanceDimensions(systems);
  const dimensions = rawDimensions.map((dim) => ({
    ...dim,
    score: ROOT_PILLAR_OVERRIDES[dim.key],
  }));
  const score =
    dimensions.length > 0
      ? Math.round(
          dimensions.reduce((sum, d) => sum + d.score, 0) / dimensions.length,
        )
      : 0;

  const coverageAvg =
    dimensions.find((d) => d.key === PillarKey.COVERAGE)?.score ?? 0;
  const classificationAvg =
    dimensions.find((d) => d.key === PillarKey.CLASSIFICATION)?.score ?? 0;
  const riskDim = dimensions.find((d) => d.key === PillarKey.RISK);
  const totalRiskScore = riskDim?.numerator ?? 0;

  return {
    score,
    dimensions,
    coverageAvg,
    classificationAvg,
    totalRiskScore,
    healthBreakdown: {
      healthy: systems.filter((s) => s.health === HealthStatus.HEALTHY).length,
      issues: systems.filter((s) => s.health === HealthStatus.ISSUES).length,
    },
    coverageTrend: [38, 42, 45, 48, 50, 52, 54, 56, 58, 60, 62, coverageAvg],
    classificationTrend: [
      22,
      24,
      26,
      28,
      30,
      32,
      34,
      36,
      38,
      40,
      42,
      classificationAvg,
    ],
    riskTrend: [
      48,
      52,
      54,
      56,
      58,
      60,
      62,
      64,
      66,
      68,
      70,
      dimensions.find((d) => d.key === PillarKey.RISK)?.score ?? 0,
    ],
  };
}

const MS_PER_HOUR = 1000 * 60 * 60;
const MS_PER_DAY = MS_PER_HOUR * 24;

export function formatFreshness(detectedAt: string): string {
  const detected = new Date(detectedAt).getTime();
  if (Number.isNaN(detected)) {
    return "—";
  }
  const diffMs = Date.now() - detected;
  if (diffMs < MS_PER_HOUR) {
    return "just now";
  }
  if (diffMs < MS_PER_DAY) {
    const hours = Math.round(diffMs / MS_PER_HOUR);
    return `${hours}h ago`;
  }
  const days = Math.round(diffMs / MS_PER_DAY);
  if (days < 30) {
    return `${days}d ago`;
  }
  const months = Math.round(days / 30);
  if (months < 12) {
    return `${months}mo ago`;
  }
  const years = Math.round(months / 12);
  return `${years}y ago`;
}

export function getRiskFreshness(detectedAt: string): RiskFreshness {
  const detected = new Date(detectedAt).getTime();
  const diffDays = (Date.now() - detected) / MS_PER_DAY;
  if (diffDays <= 7) {
    return RiskFreshness.WEEK;
  }
  if (diffDays <= 30) {
    return RiskFreshness.MONTH;
  }
  return RiskFreshness.OLDER;
}

export function latestRiskTimestamp(risks: SystemRisk[]): number {
  if (risks.length === 0) {
    return 0;
  }
  return risks.reduce((max, r) => {
    const t = new Date(r.detectedAt).getTime();
    return Number.isNaN(t) ? max : Math.max(max, t);
  }, 0);
}

export function generateSystemBriefing(system: MockSystem): string {
  const parts: string[] = [];

  parts.push(
    `${system.name} is a ${system.system_type.toLowerCase()} managed by ${system.department}.`,
  );

  if (system.risk_count > 0) {
    const riskLabels = system.risks.map((r) => r.title).join(", ");
    parts.push(
      `There ${system.risk_count === 1 ? "is" : "are"} ${system.risk_count} open risk${system.risk_count > 1 ? "s" : ""}: ${riskLabels}.`,
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
    parts.push("No purposes are defined for this system.");
  }

  if (system.risk_count === 0 && system.annotation_percent >= 80) {
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
