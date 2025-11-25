import {
  AntBreadcrumb as Breadcrumb,
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntListItemProps as ListItemProps,
  AntListProps as ListProps,
  AntSelectProps as SelectProps,
  AntTag as Tag,
  AntText as Text,
  AntTooltip as Tooltip,
  SparkleIcon,
} from "fidesui";
import _ from "lodash";

import { SeverityGauge } from "~/features/common/progress/SeverityGauge";
import { DiffStatus } from "~/types/api";
import { Page_DatastoreStagedResourceAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceAPIResponse_";

import {
  parseResourceBreadcrumbs,
  UrnBreadcrumbItem,
} from "../utils/parseResourceBreadcrumbs";
import ClassificationSelect from "./ClassificationSelect";
import styles from "./MonitorFieldListItem.module.scss";
import { MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL } from "./MonitorFields.const";
import { getMaxSeverity, mapConfidenceBucketToSeverity } from "./utils";

type TagRenderParams = Parameters<NonNullable<SelectProps["tagRender"]>>[0];

type TagRender = (
  props: TagRenderParams & {
    isFromClassifier?: boolean;
  },
) => ReturnType<NonNullable<SelectProps["tagRender"]>>;

export const tagRender: TagRender = (props) => {
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

type ListRenderItem = ListProps<
  Page_DatastoreStagedResourceAPIResponse_["items"][number]
>["renderItem"];

type MonitorFieldListItemRenderParams = Parameters<
  NonNullable<ListRenderItem>
>[0] & {
  selected?: boolean;
  onSelect?: (key: React.Key, selected: boolean) => void;
  onNavigate?: (key: string) => void;
  dataCategoriesDisabled?: boolean;
  onSetDataCategories: (urn: string, dataCategories: string[]) => void;
};

type RenderMonitorFieldListItem = (
  props: MonitorFieldListItemRenderParams & {
    actions?: ListItemProps["actions"];
  },
) => ReturnType<NonNullable<ListRenderItem>>;

const renderBreadcrumbItem = (breadcrumb: UrnBreadcrumbItem) => {
  const { title, IconComponent } = breadcrumb;
  return {
    title: IconComponent ? (
      <Flex gap={3} align="center">
        <IconComponent />
        <span>{title}</span>
      </Flex>
    ) : (
      title
    ),
  };
};

const renderMonitorFieldListItem: RenderMonitorFieldListItem = ({
  urn,
  classifications,
  name,
  diff_status,
  selected,
  onSelect,
  onSetDataCategories,
  dataCategoriesDisabled,
  onNavigate,
  preferred_data_categories,
  actions,
}) => {
  const onSelectDataCategory = (value: string) => {
    if (!preferred_data_categories?.includes(value)) {
      onSetDataCategories(urn, [...(preferred_data_categories ?? []), value]);
    }
  };

  const confidenceBucketSeverity = _(
    classifications?.flatMap(({ confidence_bucket }) => {
      const severity = confidence_bucket
        ? mapConfidenceBucketToSeverity(confidence_bucket)
        : undefined;
      return severity ? [severity] : [];
    }),
  )
    .thru(getMaxSeverity)
    .value();

  return (
    <List.Item
      key={urn}
      actions={[
        confidenceBucketSeverity && (
          <SeverityGauge severity={confidenceBucketSeverity} />
        ),
        ...(actions ?? []),
      ]}
    >
      <List.Item.Meta
        avatar={
          <div className="ml-2">
            <Checkbox
              checked={selected}
              onChange={(e) => onSelect && onSelect(urn, e.target.checked)}
            />
          </div>
        }
        title={
          <Flex
            gap={12}
            align="center"
            className={styles["monitor-field__title"]}
          >
            <Button
              type="text"
              size="small"
              className="-mx-2"
              onClick={() => onNavigate && onNavigate(urn)}
            >
              {name}
            </Button>
            {diff_status && diff_status !== DiffStatus.ADDITION && (
              <Tag
                bordered={false}
                color={
                  MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[diff_status].color
                }
              >
                {MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL[diff_status].label}
              </Tag>
            )}
            <Tooltip title={urn} mouseEnterDelay={0.5}>
              <Breadcrumb
                className={styles["monitor-field__breadcrumb"]}
                items={parseResourceBreadcrumbs(urn).map(renderBreadcrumbItem)}
                // @ts-expect-error - role works here, but Ant's type system doesn't know that
                role="presentation"
                style={{
                  overflow: "hidden",
                }}
              />
            </Tooltip>
          </Flex>
        }
        description={
          <ClassificationSelect
            mode="multiple"
            value={preferred_data_categories ?? []}
            urn={urn}
            tagRender={(props) => {
              const isFromClassifier = !!classifications?.find(
                (item) => item.label === props.value,
              );

              const handleClose = () => {
                const newDataCategories =
                  preferred_data_categories?.filter(
                    (category) => category !== props.value,
                  ) ?? [];
                onSetDataCategories(urn, newDataCategories);
              };

              return tagRender({
                ...props,
                isFromClassifier,
                onClose: handleClose,
              });
            }}
            onSelectDataCategory={onSelectDataCategory}
            disabled={dataCategoriesDisabled}
          />
        }
      />
    </List.Item>
  );
};
export default renderMonitorFieldListItem;
