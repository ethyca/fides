import {
  AntButton as Button,
  AntFlex as Flex,
  AntFlexProps as FlexProps,
  AntTag as Tag,
  AntTagProps as TagProps,
  AntText as Text,
} from "fidesui";
import { ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import { COLLAPSE_BUTTON_TEXT, TAG_MAX_WIDTH } from "./constants";
import { ColumnState } from "./types";

type TagExpandableCellValues = {
  label: string | ReactNode;
  key: string;
  /**
   * Per-value props to pass to the Tag component.
   */
  tagProps?: TagProps;
}[];
export interface TagExpandableCellProps extends Omit<FlexProps, "children"> {
  values: TagExpandableCellValues | undefined;
  columnState?: ColumnState;
  onStateChange?: (isExpanded: boolean) => void;
  onTagClose?: (key: string) => void;
  tagProps?: TagProps;
}

/**
 * A cell that displays a list of tags and a button to expand the list.
 * Click the cell to collapse the list.
 * @param values - The values to display in the cell.
 * @param columnState - The state of the column.
 * @param tagProps - The props to pass to the Tag component.  If a value has a `tagProps` property, it will override the tagProps set at the component level.
 */
export const TagExpandableCell = ({
  values,
  columnState,
  tagProps,
  onTagClose,
  onStateChange,
  ...props
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
    } else {
      setDisplayValues(values);
    }
  }, [isCollapsed, values, onStateChange]);

  useEffect(() => {
    if (values?.length && values.length <= displayThreshold && !isCollapsed) {
      setIsCollapsed(true);
      onStateChange?.(false);
    }
  }, [values, onStateChange, isCollapsed]);

  const handleCollapse = useCallback(() => {
    // if we don't also set displayValues here, there's a UI glitch where the tags stop wrapping before they become collapsed which in turn can cause the table to scroll.
    setDisplayValues(values?.slice(0, displayThreshold));
    setIsCollapsed(true);
    onStateChange?.(false);
  }, [values, onStateChange]);

  const handleExpand = useCallback(() => {
    setIsCollapsed(false);
    onStateChange?.(true);
  }, [onStateChange]);

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
        style={{ overflowX: "auto", ...props.style }}
        {...props}
      >
        {displayValues.map((value) => (
          <Tag
            color="white"
            key={value.key}
            data-testid={value.key}
            onClose={onTagClose ? () => onTagClose(value.key) : undefined}
            {...tagProps}
            {...value.tagProps}
          >
            <Text
              ellipsis={isCollapsed ? { tooltip: true } : false}
              style={{
                color: "inherit",
                maxWidth: isCollapsed ? TAG_MAX_WIDTH : undefined,
              }}
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
    props,
    values,
    tagProps,
    onTagClose,
    handleToggle,
  ]);
};
