import type {
  AssessmentGroupResponse,
  PrivacyAssessmentResponse,
} from "~/features/privacy-assessments/types";
import {
  AssessmentStatus,
  RiskLevel,
} from "~/features/privacy-assessments/types";

const assessment = (
  overrides: Partial<PrivacyAssessmentResponse> &
    Pick<PrivacyAssessmentResponse, "id" | "status">,
): PrivacyAssessmentResponse =>
  ({
    name: `Assessment ${overrides.id}`,
    risk_level: null,
    created_by: null,
    ...overrides,
  }) as PrivacyAssessmentResponse;

export const mockAssessmentGroups: AssessmentGroupResponse[] = [
  {
    data_use: "marketing.advertising",
    data_use_name: "Marketing & Advertising",
    system_count: 4,
    assessments: [
      assessment({
        id: "a1",
        status: AssessmentStatus.IN_PROGRESS,
        risk_level: RiskLevel.HIGH,
        created_by: "casey@example.com",
      }),
      assessment({
        id: "a2",
        status: AssessmentStatus.OUTDATED,
        risk_level: RiskLevel.HIGH,
        created_by: "casey@example.com",
      }),
      assessment({
        id: "a3",
        status: AssessmentStatus.IN_PROGRESS,
        risk_level: RiskLevel.MEDIUM,
        created_by: "jordan@example.com",
      }),
      assessment({
        id: "a4",
        status: AssessmentStatus.COMPLETED,
        risk_level: RiskLevel.LOW,
        created_by: "casey@example.com",
      }),
    ],
  },
  {
    data_use: "personalize.content",
    data_use_name: "Personalization",
    system_count: 3,
    assessments: [
      assessment({
        id: "b1",
        status: AssessmentStatus.OUTDATED,
        risk_level: RiskLevel.HIGH,
        created_by: "morgan@example.com",
      }),
      assessment({
        id: "b2",
        status: AssessmentStatus.GENERATING,
        risk_level: null,
        created_by: "morgan@example.com",
      }),
      assessment({
        id: "b3",
        status: AssessmentStatus.COMPLETED,
        risk_level: RiskLevel.MEDIUM,
        created_by: "alex@example.com",
      }),
    ],
  },
  {
    data_use: "essential.service",
    data_use_name: "Essential Service",
    system_count: 5,
    assessments: [
      assessment({
        id: "c1",
        status: AssessmentStatus.COMPLETED,
        risk_level: RiskLevel.LOW,
        created_by: "alex@example.com",
      }),
      assessment({
        id: "c2",
        status: AssessmentStatus.COMPLETED,
        risk_level: RiskLevel.LOW,
        created_by: "jordan@example.com",
      }),
      assessment({
        id: "c3",
        status: AssessmentStatus.IN_PROGRESS,
        risk_level: RiskLevel.MEDIUM,
        created_by: "sam@example.com",
      }),
    ],
  },
  {
    data_use: "improve.system",
    data_use_name: "Product Analytics",
    system_count: 2,
    assessments: [
      assessment({
        id: "d1",
        status: AssessmentStatus.IN_PROGRESS,
        risk_level: RiskLevel.MEDIUM,
        created_by: "riley@example.com",
      }),
      assessment({
        id: "d2",
        status: AssessmentStatus.OUTDATED,
        risk_level: RiskLevel.LOW,
        created_by: "taylor@example.com",
      }),
    ],
  },
];
