import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntTypography as Typography,
} from "fidesui";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import styles from "./Cells.module.scss";
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
  const flexRef = useRef<HTMLDivElement>(null); // for focus management
  const buttonRef = useRef<HTMLButtonElement>(null); // for focus management

  useEffect(() => {
    // Also reset isCollapsed state when version changes.
    // This is to handle the case where the user expands cells individually.
    // "Expand/Collapse All" will not be reapplied otherwise.
    setIsCollapsed(!isExpanded);
  }, [isExpanded, version]);

  const handleCollapse = useCallback(() => {
    setIsCollapsed(true);
    setTimeout(() => {
      buttonRef.current?.focus();
    }, 0);
  }, []);

  const handleExpand = useCallback(() => {
    setIsCollapsed(false);
    setTimeout(() => {
      flexRef.current?.focus();
    }, 0);
  }, []);

  return useMemo(() => {
    if (!values?.length) {
      return null;
    }

    if (values.length === 1) {
      return <Text ellipsis>{values[0]}</Text>;
    }

    return (
      <Flex
        ref={flexRef}
        align="center"
        gap="small"
        className={`${styles.cellBleed} ${!isCollapsed ? styles.cellHover : ""}`}
        onClick={(e) => {
          e.stopPropagation();
          if (!isCollapsed) {
            handleCollapse();
          }
        }}
        onKeyDown={(e) => {
          e.stopPropagation();
          if (e.key === "Enter" || e.key === " ") {
            handleCollapse();
          }
        }}
        role={!isCollapsed ? "button" : undefined}
        tabIndex={!isCollapsed ? 0 : undefined}
      >
        {isCollapsed && (
          <>
            <Text ellipsis>
              {values.length} {valueSuffix}
            </Text>
            <Button
              ref={buttonRef}
              type="link"
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleExpand();
              }}
              className="p-0 text-xs"
            >
              View
            </Button>
          </>
        )}
        {!isCollapsed && (
          <List dataSource={values} renderItem={(item) => <li>{item}</li>} />
        )}
      </Flex>
    );
  }, [isCollapsed, values, valueSuffix, handleCollapse, handleExpand]);
};
