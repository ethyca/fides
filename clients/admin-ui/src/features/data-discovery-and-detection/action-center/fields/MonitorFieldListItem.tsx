import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntListProps as ListProps,
  AntProgress as Progress,
  AntTag as Tag,
  AntText as Text,
  Icons,
  SparkleIcon,
} from "fidesui";

import { capitalize } from "~/features/common/utils";
import { DiffStatus } from "~/types/api";
import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";
import { Page_DatastoreStagedResourceAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceAPIResponse_";

import { RESOURCE_STATUS } from "./useFilters";

type ResourceStatusLabel = (typeof RESOURCE_STATUS)[number];
type ResourceStatusLabelColor = "nectar" | "red" | "orange" | "blue";

const ResourceStatus: Record<
  DiffStatus,
  {
    label: ResourceStatusLabel;
    color?: ResourceStatusLabelColor;
  }
> = {
  classifying: { label: "Classifying", color: "blue" },
  classification_queued: { label: "Classifying", color: "blue" },
  classification_update: { label: "Classifying", color: "nectar" },
  classification_addition: { label: "In Review", color: "blue" },
  addition: { label: "In Review", color: "blue" },
  muted: { label: "Unmonitored", color: "nectar" },
  removal: { label: "Attention Required", color: "red" },
  removing: { label: "In Review", color: "nectar" },
  promoting: { label: "In Review", color: "nectar" },
  monitored: { label: "Approved", color: "nectar" },
} as const;

const MonitorFieldListItem: ListProps<
  Page_DatastoreStagedResourceAPIResponse_["items"][number]
>["renderItem"] = ({
  urn,
  classifications,
  name,
  diff_status,
  user_assigned_data_categories,
}) => {
  return (
    <List.Item
      key={urn}
      actions={[
        classifications && classifications.length > 0 && (
          <Flex
            gap="small"
            align="center"
            className="pr-[var(--ant-padding-xl)]"
            key="progress"
          >
            <Progress
              percent={
                classifications.find(
                  (classification) =>
                    classification.confidence_score ===
                    ConfidenceScoreRange.HIGH,
                )
                  ? 100
                  : 25
              }
              percentPosition={{
                align: "start",
                type: "outer",
              }}
              strokeColor={
                classifications.find(
                  (classification) =>
                    classification.confidence_score ===
                    ConfidenceScoreRange.HIGH,
                )
                  ? "var(--ant-color-success-text)"
                  : "var(--ant-color-warning-text)"
              }
              steps={2}
              showInfo={false}
              strokeLinecap="round"
              size={[24, 8]}
            />
            <Text size="sm" type="secondary" className="font-normal">
              {capitalize(
                classifications.find(
                  (classification) =>
                    classification.confidence_score ===
                    ConfidenceScoreRange.HIGH,
                )
                  ? ConfidenceScoreRange.HIGH
                  : ConfidenceScoreRange.LOW,
              )}
            </Text>
          </Flex>
        ),
        classifications && classifications.length > 0 && (
          <Button icon={<Icons.Checkmark />} size="small" key="approve" />
        ),
        classifications && classifications.length > 0 && (
          <Button icon={<Icons.Close />} size="small" key="deny" />
        ),
        <Button icon={<SparkleIcon />} size="small" key="reclassify" />,
      ]}
    >
      <List.Item.Meta
        avatar={<Checkbox />}
        title={
          <Flex justify="space-between">
            <Flex gap="small" align="center" className="w-full">
              {name}
              {diff_status && (
                <Tag
                  bordered={false}
                  color={ResourceStatus[diff_status].color}
                  className="font-normal text-[var(--ant-font-size-sm)]"
                >
                  {ResourceStatus[diff_status].label}
                </Tag>
              )}
              <Text
                size="sm"
                type="secondary"
                className="overflow-hidden font-normal"
                ellipsis={{ tooltip: urn }}
              >
                {urn}
              </Text>
            </Flex>
          </Flex>
        }
        description={
          <>
            <Button type="text" icon={<Icons.Add />} size="small" />
            {classifications?.map((c) => (
              <Tag
                bordered
                color="white"
                closable
                icon={<SparkleIcon />}
                className="text-[var(--ant-color-text)]"
                key={c.label}
              >
                {c.label}
              </Tag>
            ))}
            {user_assigned_data_categories?.map((c) => (
              <Tag
                bordered
                color="white"
                closable
                className="text-[var(--ant-color-text)]"
                key={c}
              >
                {c}
              </Tag>
            ))}
          </>
        }
      />
    </List.Item>
  );
};
export default MonitorFieldListItem;
