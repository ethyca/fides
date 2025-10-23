import {
  AntBreadcrumb as Breadcrumb,
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntListProps as ListProps,
  AntSelectProps as SelectProps,
  AntTag as Tag,
  AntText as Text,
  Icons,
  SparkleIcon,
} from "fidesui";

import { ClassifierProgress } from "~/features/classifier/ClassifierProgress";
import { DiffStatus } from "~/types/api";
import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";
import { Page_DatastoreStagedResourceAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceAPIResponse_";

import {
  parseResourceBreadcrumbs,
  UrnBreadcrumbItem,
} from "../utils/parseResourceBreadcrumbs";
import ClassificationSelect from "./ClassificationSelect";
import styles from "./MonitorFieldListItem.module.scss";
import { MAP_DIFF_STATUS_TO_RESOURCE_STATUS_LABEL } from "./MonitorFields.const";

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
  onSelect?: (key: string, selected?: boolean) => void;
  onSetDataCategories: (dataCategories: string[], urn: string) => void;
  onNavigate?: (key: string) => void;
  onIgnore: (urn: string) => void;
};

type RenderMonitorFieldListItem = (
  props: MonitorFieldListItemRenderParams,
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
  onNavigate,
  user_assigned_data_categories,
  onIgnore,
}) => {
  const onSelectDataCategory = (value: string) => {
    if (
      classifications?.find((classification) => classification.label === value)
    ) {
      return;
    }

    if (!user_assigned_data_categories?.includes(value)) {
      onSetDataCategories(
        [...(user_assigned_data_categories ?? []), value],
        urn,
      );
    }
  };

  return (
    <List.Item
      key={urn}
      actions={[
        classifications && classifications.length > 0 && (
          <ClassifierProgress
            percent={
              classifications.find(
                (classification) =>
                  classification.confidence_score === ConfidenceScoreRange.HIGH,
              )
                ? 100
                : 25
            }
          />
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
          icon={<SparkleIcon size={12} />}
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
            <Breadcrumb
              className={styles["monitor-field__breadcrumb"]}
              items={parseResourceBreadcrumbs(urn).map(renderBreadcrumbItem)}
              // @ts-expect-error - role works here, but Ant's type system doesn't know that
              role="presentation"
            />
          </Flex>
        }
        description={
          <ClassificationSelect
            mode="tags"
            value={[
              ...(classifications?.map(({ label }) => label) ?? []),
              ...(user_assigned_data_categories?.map((value) => value) ?? []),
            ]}
            tagRender={(props) => {
              const isFromClassifier = !!classifications?.find(
                (item) => item.label === props.value,
              );

              // TODO: This is temporary, it will be fixed in https://ethyca.atlassian.net/browse/ENG-1687
              const closable =
                !isFromClassifier &&
                !!user_assigned_data_categories &&
                user_assigned_data_categories.includes(props.value);

              const handleClose = () => {
                if (closable) {
                  const newDataCategories =
                    user_assigned_data_categories?.filter(
                      (category) => category !== props.value,
                    ) ?? [];
                  onSetDataCategories(newDataCategories, urn);
                }
              };

              return tagRender({
                ...props,
                isFromClassifier,
                closable,
                onClose: handleClose,
              });
            }}
            onSelectDataCategory={onSelectDataCategory}
          />
        }
      />
    </List.Item>
  );
};
export default renderMonitorFieldListItem;
