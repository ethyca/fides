import {
  AntButton as Button,
  AntFlex as Flex,
  AntTag as Tag,
  AntTagProps as TagProps,
  AntText as Text,
} from "fidesui";
import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import { COLLAPSE_BUTTON_TEXT, TAG_MAX_WIDTH } from "./constants";
import { ColumnState } from "./types";

type TagExpandableCellValues = { label: string | ReactNode; key: string }[];

interface TagExpandableCellProps extends Omit<TagProps, "onClose"> {
  values: TagExpandableCellValues | undefined;
  columnState?: ColumnState;
  onClose?: (key: string) => void;
}

/**
 * A cell that displays a list of tags and a button to expand the list.
 * Click the cell to collapse the list.
 * @param values - The values to display in the cell.
 * @param columnState - The state of the column.
 * @param tagProps - The props to pass to the Tag component.
 */
export const TagExpandableCell = ({
  values,
  columnState,
  onClose,
  ...tagProps
}: TagExpandableCellProps) => {
  const { isExpanded, isWrapped, version } = columnState || {};
  const displayThreshold = 2; // Number of badges to display when collapsed
  const [isCollapsed, setIsCollapsed] = useState<boolean>(!isExpanded);
  const [isWrappedState, setIsWrappedState] = useState<boolean>(!!isWrapped);
  const [displayValues, setDisplayValues] = useState<
    TagExpandableCellValues | undefined
  >(!isExpanded ? values?.slice(0, displayThreshold) : values);
  useEffect(() => {
    // Also reset isCollapsed state when version changes.
    // This is to handle the case where the user expands cells individually.
    // "Expand/Collapse All" will not be reapplied otherwise.
    setIsCollapsed(!isExpanded);
  }, [isExpanded, version]);

  useEffect(() => {
    setIsWrappedState(!!isWrapped);
  }, [isWrapped]);

  useEffect(() => {
    if (values?.length) {
      // This also handles column header expand/collapse
      setDisplayValues(
        isCollapsed ? values.slice(0, displayThreshold) : values,
      );
    }
  }, [isCollapsed, values]);

  const handleCollapse = useCallback(() => {
    // if we don't also set displayValues here, there's a UI glitch where the tags stop wrapping before they become collapsed which in turn can cause the table to scroll.
    setDisplayValues(values?.slice(0, displayThreshold));
    setIsCollapsed(true);
  }, [values]);

  const handleExpand = useCallback(() => {
    setIsCollapsed(false);
  }, []);

  const handleToggle = useCallback(() => {
    if (isCollapsed) {
      handleExpand();
    } else {
      handleCollapse();
    }
  }, [isCollapsed, handleExpand, handleCollapse]);

  return useMemo(() => {
    if (!displayValues?.length) {
      return <span data-testid="tag-expandable-cell-empty" />;
    }
    return (
      <Flex
        align={isCollapsed ? "center" : "start"}
        wrap={isWrappedState ? "wrap" : "nowrap"}
        vertical={!isCollapsed}
        gap="small"
        data-testid="tag-expandable-cell"
      >
        {displayValues.map((value) => (
          <Tag
            color="white"
            key={value.key}
            data-testid={value.key}
            onClose={() => onClose?.(value.key)}
            {...tagProps}
          >
            <Text
              ellipsis={isCollapsed ? { tooltip: true } : false}
              style={isCollapsed ? { maxWidth: TAG_MAX_WIDTH } : {}}
            >
              {value.label}
            </Text>
          </Tag>
        ))}
        {values && values.length > displayThreshold && (
          <Button
            type="link"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              handleToggle();
            }}
            className="h-auto p-0"
            style={{
              fontSize: "var(--ant-font-size)",
            }}
          >
            {isCollapsed
              ? `+${values.length - displayThreshold} more`
              : COLLAPSE_BUTTON_TEXT}
          </Button>
        )}
      </Flex>
    );
  }, [
    displayValues,
    isCollapsed,
    isWrappedState,
    values,
    tagProps,
    onClose,
    handleToggle,
  ]);
};
