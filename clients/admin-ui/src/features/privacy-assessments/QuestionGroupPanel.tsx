import {
  Badge,
  Button,
  CUSTOM_TAG_COLOR,
  Flex,
  Icons,
  Tag,
  Text,
} from "fidesui";

import { RISK_LEVEL_DOT_COLORS, RISK_LEVEL_LABELS } from "./constants";
import { QuestionGroup } from "./types";
import { getInitials, getTimeSince } from "./utils";

interface QuestionGroupPanelProps {
  group: QuestionGroup;
  isExpanded: boolean;
}

export const QuestionGroupPanel = ({
  group,
  isExpanded,
}: QuestionGroupPanelProps) => {
  const answeredCount = group.questions.filter(
    (q) => q.answer_text.trim().length > 0,
  ).length;
  const totalCount = group.questions.length;
  const isGroupCompleted = answeredCount === totalCount;

  return (
    <>
      <Flex gap="large" align="flex-start" className="min-w-0 flex-1">
        <div className="flex-1">
          <Text strong size="lg" className="mb-3 block">
            {group.id}. {group.title}
          </Text>
          <Flex gap="middle" align="center" wrap="wrap" className="mb-2">
            <Text type="secondary" size="sm">
              {group.last_updated_at
                ? `Updated ${getTimeSince(group.last_updated_at)}`
                : "Not updated yet"}
              {group.last_updated_by && (
                <>
                  {" by "}
                  <Tag color={CUSTOM_TAG_COLOR.DEFAULT} className="ml-1">
                    {getInitials(group.last_updated_by)}
                  </Tag>
                </>
              )}
            </Text>
            <Text type="secondary" size="sm">
              <Text strong size="sm">
                Fields:
              </Text>{" "}
              {answeredCount}/{totalCount}
            </Text>
            {group.risk_level && (
              <Flex gap="small" align="center">
                <Badge color={RISK_LEVEL_DOT_COLORS[group.risk_level]} />
                <Text size="sm">
                  Risk: {RISK_LEVEL_LABELS[group.risk_level]}
                </Text>
              </Flex>
            )}
          </Flex>
          {isExpanded && (
            <Flex align="center" gap="small" className="mt-3">
              <Button
                type="default"
                icon={<Icons.Document />}
                size="small"
                disabled
              >
                View evidence
              </Button>
            </Flex>
          )}
        </div>
      </Flex>
      <div className="absolute right-6 top-4">
        <Tag
          color={
            isGroupCompleted
              ? CUSTOM_TAG_COLOR.SUCCESS
              : CUSTOM_TAG_COLOR.DEFAULT
          }
        >
          {isGroupCompleted ? "Completed" : "Pending"}
        </Tag>
      </div>
    </>
  );
};
