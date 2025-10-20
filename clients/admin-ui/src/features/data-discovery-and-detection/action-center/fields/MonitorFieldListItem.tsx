import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntProgress as Progress,
  AntSelectProps as SelectProps,
  AntTag as Tag,
  AntText as Text,
  Icons,
  SparkleIcon,
} from "fidesui";
import { useHotkeys } from "react-hotkeys-hook";

import { TaxonomySelectProps } from "~/features/common/dropdown/TaxonomySelect";
import { capitalize } from "~/features/common/utils";
import { DiffStatus } from "~/types/api";
import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";
import { Page_DatastoreStagedResourceAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceAPIResponse_";

import ClassificationSelect from "./ClassificationSelect";
import styles from "./MonitorFieldListItem.module.scss";
import { MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL } from "./MonitorFields.const";

type TagRenderParams = Parameters<NonNullable<SelectProps["tagRender"]>>[0];

type TagRender = (
  props: TagRenderParams & {
    isFromClassifier?: boolean;
  },
) => ReturnType<NonNullable<SelectProps["tagRender"]>>;

const tagRender: TagRender = (props) => {
  const { label, closable, onClose, isFromClassifier } = props;

  const onPreventMouseDown = (event: React.MouseEvent<HTMLSpanElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  return (
    <Tag
      color="white"
      bordered
      onMouseDown={onPreventMouseDown}
      closable={closable}
      onClose={onClose}
      /** Style required because of tailwind limitations and our ui package presets */
      style={{
        marginInlineEnd: "calc((var(--ant-padding-xs) * 0.5))",
      }}
      icon={isFromClassifier && <SparkleIcon />}
    >
      <Text size="sm">{label}</Text>
    </Tag>
  );
};

type MonitorFieldListItemProps =
  Page_DatastoreStagedResourceAPIResponse_["items"][number] & {
    selected?: boolean;
    focused?: boolean;
    onSelect?: (key: string, selected?: boolean) => void;
    onSetDataCategories: (dataCategories: string[], urn: string) => void;
    onIgnore: (urn: string) => void;
    index: number;
  };

const MonitorFieldListItem = ({
  urn,
  classifications,
  name,
  diff_status,
  selected,
  focused,
  onSelect,
  onSetDataCategories,
  user_assigned_data_categories,
  onIgnore,
  index,
}: MonitorFieldListItemProps) => {
  const onChange: TaxonomySelectProps["onChange"] = (values: string[]) => {
    onSetDataCategories(
      values.flatMap((value) =>
        !classifications?.find(
          (classification) => classification.label !== value,
        )
          ? [value]
          : [],
      ),
      urn,
    );
  };

  // Handle space bar to toggle selection when focused
  useHotkeys(
    "space",
    (e) => {
      if (focused && onSelect) {
        e.preventDefault(); // Prevent page scroll
        onSelect(urn, !selected);
      }
    },
    { enabled: focused },
    [focused, selected, urn, onSelect],
  );

  return (
    <List.Item
      key={urn}
      tabIndex={-1}
      id={`field-item-${index}`}
      className={`${focused ? styles["list-item--focused"] : ""}`}
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
          <Button
            aria-label="Approve"
            icon={<Icons.Checkmark />}
            size="small"
            key="approve"
          />
        ),
        diff_status !== DiffStatus.MUTED && (
          <Button
            icon={<Icons.ViewOff />}
            size="small"
            aria-label="Ignore"
            key="ignore"
            onClick={() => onIgnore(urn)}
          />
        ),
        <Button
          aria-label="Reclassify"
          icon={<SparkleIcon />}
          size="small"
          key="reclassify"
        />,
      ]}
    >
      <List.Item.Meta
        avatar={
          <Checkbox
            checked={selected}
            onChange={(e) => onSelect && onSelect(urn, e.target.checked)}
          />
        }
        title={
          <Flex justify="space-between">
            <Flex gap="small" align="center" className="w-full">
              {name}
              {diff_status && (
                <Tag
                  bordered={false}
                  color={
                    MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[diff_status].color
                  }
                  className="font-normal text-[var(--ant-font-size-sm)]"
                >
                  {MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[diff_status].label}
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
          <ClassificationSelect
            mode="tags"
            value={[
              ...(classifications?.map(({ label }) => label) ?? []),
              ...(user_assigned_data_categories?.map((value) => value) ?? []),
            ]}
            tagRender={(props) =>
              tagRender({
                ...props,
                isFromClassifier: !!classifications?.find(
                  (item) => item.label === props.value,
                ),
              })
            }
            onChange={onChange}
          />
        }
      />
    </List.Item>
  );
};

export default MonitorFieldListItem;
