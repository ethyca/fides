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

import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import { TagList } from "~/features/common/TagList";
import {
  ASSESSMENT_STATUS_LABELS,
  RISK_LEVEL_LABELS,
  RISK_TAG_COLORS,
  STATUS_COLORS,
} from "~/features/privacy-assessments/constants";

import { PrivacyAssessmentResponse } from "./types";

const { Title } = Typography;

interface AssessmentCardProps {
  assessment: PrivacyAssessmentResponse;
  onClick: () => void;
}

export const AssessmentCard = ({
  assessment,
  onClick,
}: AssessmentCardProps) => {
  const { getDataCategoryDisplayName } = useTaxonomies();

  // Do not assume defaults for missing values; show "N/A" when absent
  const riskLevel = assessment.risk_level ?? null;
  const status = assessment.status ?? null;
  const completeness = assessment.completeness ?? 0;

  const riskLabel = riskLevel ? RISK_LEVEL_LABELS[riskLevel] : "N/A";
  const statusLabel = status ? ASSESSMENT_STATUS_LABELS[status] : "N/A";
  const isComplete = completeness === 100;

  return (
    <Card
      className="flex min-w-[280px] flex-col"
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
    >
      <Flex vertical gap="small" className="flex-1" justify="space-between">
        <div>
          <Title level={5} className="!mb-2">
            {assessment.name}
          </Title>
          <Text type="secondary" className="mb-2 block text-xs">
            System: {assessment.system_name ?? ""}
          </Text>
          {(assessment.data_categories ?? []).length > 0 && (
            <Text type="secondary" className="mb-2 block text-xs leading-6">
              Processing{" "}
              <TagList
                tags={(assessment.data_categories ?? []).map((key) => ({
                  value: key,
                  label: getDataCategoryDisplayName(key),
                }))}
                maxTags={1}
                expandable
              />{" "}
              for{" "}
              <TagList
                tags={
                  assessment.data_use_name ? [assessment.data_use_name] : []
                }
                maxTags={1}
              />
            </Text>
          )}
          {riskLevel && (
            <div>
              <Tag
                color={RISK_TAG_COLORS[riskLabel] ?? CUSTOM_TAG_COLOR.DEFAULT}
              >
                {`${riskLabel} risk`}
              </Tag>
            </div>
          )}
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
                  style={{ color: STATUS_COLORS[status] }}
                >
                  {statusLabel}
                </Text>
                <Button type="link" className="!p-0" onClick={onClick}>
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
