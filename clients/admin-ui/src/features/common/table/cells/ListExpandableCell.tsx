import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntTypography as Typography,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { COLLAPSE_BUTTON_TEXT } from "./constants";
import { ColumnState } from "./types";

const { Text } = Typography;

/**
 * A cell that displays a single value or a count of values and a button to
 * expand the list. Click the cell to collapse the list.
 * @param values - The values to display in the cell.
 * @param valueSuffix - The suffix to display in the cell.
 * @param columnState - The state of the column.
 */
export const ListExpandableCell = ({
  values,
  valueSuffix,
  columnState,
}: {
  values: string[] | undefined;
  valueSuffix: string;
  columnState?: ColumnState;
}) => {
  const { isExpanded, version } = columnState || {};
  const [isCollapsed, setIsCollapsed] = useState<boolean>(!isExpanded);

  useEffect(() => {
    // Also reset isCollapsed state when version changes.
    // This is to handle the case where the user expands cells individually.
    // "Expand/Collapse All" will not be reapplied otherwise.
    setIsCollapsed(!isExpanded);
  }, [isExpanded, version]);

  const handleCollapse = useCallback(() => {
    setIsCollapsed(true);
  }, []);

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
    if (!values?.length) {
      return null;
    }

    if (values.length === 1) {
      return <Text ellipsis>{values[0]}</Text>;
    }

    return (
      <Flex
        align={isCollapsed ? "center" : "flex-start"}
        vertical={!isCollapsed}
        gap="small"
      >
        {isCollapsed ? (
          <Text ellipsis>
            {values.length} {valueSuffix}
          </Text>
        ) : (
          <List dataSource={values} renderItem={(item) => <li>{item}</li>} />
        )}
        <Button
          type="link"
          size="small"
          onClick={(e) => {
            e.stopPropagation();
            handleToggle();
          }}
          className="p-0 text-xs"
        >
          {isCollapsed ? "view" : COLLAPSE_BUTTON_TEXT}
        </Button>
      </Flex>
    );
  }, [isCollapsed, values, valueSuffix, handleToggle]);
};
