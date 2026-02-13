import {
  Button,
  Card,
  CUSTOM_TAG_COLOR,
  Flex,
  Tag,
  Text,
  Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

import { PrivacyAssessmentResponse } from "~/features/privacy-assessments";
import {
  ASSESSMENT_STATUS_LABELS,
  RISK_LEVEL_LABELS,
} from "~/features/privacy-assessments/constants";

const { Title } = Typography;

interface AssessmentCardProps {
  assessment: PrivacyAssessmentResponse;
  onClick: () => void;
}

const getRiskTagColor = (riskLevel: string): CUSTOM_TAG_COLOR => {
  const colors: Record<string, CUSTOM_TAG_COLOR> = {
    High: CUSTOM_TAG_COLOR.ERROR,
    Med: CUSTOM_TAG_COLOR.WARNING,
    Low: CUSTOM_TAG_COLOR.DEFAULT,
  };
  return colors[riskLevel] ?? CUSTOM_TAG_COLOR.DEFAULT;
};

const getStatusColor = (status: string): string | undefined => {
  if (status === "completed") {
    return palette.FIDESUI_SUCCESS;
  }
  if (status === "outdated") {
    return palette.FIDESUI_ERROR;
  }
  return undefined;
};

export const AssessmentCard = ({
  assessment,
  onClick,
}: AssessmentCardProps) => {
  const riskLevel = assessment.risk_level ?? "low";
  const status = assessment.status ?? "in_progress";
  const completeness = assessment.completeness ?? 0;
  const dataCategories = assessment.data_categories ?? [];
  const systemName = assessment.system_name ?? "";
  const dataUseName = assessment.data_use_name ?? "";

  const riskLabel = RISK_LEVEL_LABELS[riskLevel];
  const statusLabel = ASSESSMENT_STATUS_LABELS[status];
  const isComplete = completeness === 100;

  return (
    <Card
      hoverable
      className="flex min-w-[280px] cursor-pointer flex-col"
      style={{
        width: "calc((100% - 48px) / 4)",
        ...(isComplete && {
          borderLeft: `4px solid ${palette.FIDESUI_SUCCESS}`,
        }),
      }}
      styles={{
        body: {
          display: "flex",
          flexDirection: "column",
          flex: 1,
        },
      }}
      onClick={onClick}
    >
      <Flex vertical gap="small" className="flex-1" justify="space-between">
        <div>
          <Title level={5} className="!mb-2">
            {assessment.name}
          </Title>
          <Text type="secondary" className="mb-2 block text-xs">
            System: {systemName}
          </Text>
          {dataCategories.length > 0 && (
            <Text type="secondary" className="mb-2 block text-xs leading-6">
              Processing{" "}
              {dataCategories.map((category: string, idx: number) => (
                <span key={category}>
                  <Tag
                    color={CUSTOM_TAG_COLOR.DEFAULT}
                    className="!m-0 align-middle text-[11px]"
                  >
                    {category}
                  </Tag>
                  {idx < dataCategories.length - 1 && " "}
                </span>
              ))}{" "}
              for{" "}
              <Tag
                color={CUSTOM_TAG_COLOR.DEFAULT}
                className="!m-0 align-middle text-[11px]"
              >
                {dataUseName}
              </Tag>
            </Text>
          )}
          <div>
            <Tag color={getRiskTagColor(riskLabel)}>{riskLabel} risk</Tag>
          </div>
        </div>

        <div className="mt-4 border-t border-gray-100 pt-4">
          {isComplete ? (
            <Flex
              align="center"
              gap="middle"
              className="rounded-lg p-3"
              style={{ backgroundColor: `${palette.FIDESUI_SUCCESS}10` }}
            >
              <div
                className="flex size-7 items-center justify-center rounded-full"
                style={{ backgroundColor: palette.FIDESUI_SUCCESS }}
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 32 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M13 24L4 15L6.5 12.5L13 19L25.5 6.5L28 9L13 24Z"
                    fill="white"
                  />
                </svg>
              </div>
              <div>
                <Text
                  strong
                  className="block text-sm"
                  style={{ color: palette.FIDESUI_SUCCESS }}
                >
                  Assessment complete
                </Text>
                <Text type="secondary" className="text-xs">
                  {statusLabel}
                </Text>
              </div>
            </Flex>
          ) : (
            <>
              <Flex justify="space-between" className="mb-2">
                <Text type="secondary" className="text-xs">
                  Completeness
                </Text>
                <Text strong className="text-xs">
                  {completeness}%
                </Text>
              </Flex>
              <div className="h-1.5 overflow-hidden rounded bg-gray-100">
                <div
                  className="h-full"
                  style={{
                    width: `${completeness}%`,
                    backgroundColor: palette.FIDESUI_MINOS,
                  }}
                />
              </div>
              <Flex justify="space-between" align="center" className="mt-2">
                <Text
                  className="text-[11px]"
                  style={{ color: getStatusColor(status) }}
                >
                  {statusLabel}
                </Text>
                <Button type="link" className="!p-0">
                  Resume
                </Button>
              </Flex>
            </>
          )}
        </div>
      </Flex>
    </Card>
  );
};
