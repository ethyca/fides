import React from "react";
import { useSelector } from "react-redux";
import { ColumnInstance, Row } from "react-table";

import { selectDataCategoriesMap } from "~/features/taxonomy";

/**
 * This filter uses the hierarchy of fides keys to determine which rows are selected.
 * For example, given a table like:
 *  | #  |  Categories        |
 *  | -- | --                 |
 *  | 1  |  user.contact      |
 *  | 2  |  user.name         |
 *  | 3  |  system.operations |
 * The user could filter with a tree of checkboxes:
 *   - "user" = Rows 1 & 2
 *   - "user.contact" = Only row 1
 *   - "system" = Only row 2
 */
export const checkboxTreeFilter = <D extends Record<string, unknown>>(
  rows: Row<D>[],
  columnIds: string[],
  filterValue: string[]
) => {
  // The useFilters hook passes a single column id.
  const columnId = columnIds[0];
  const filterValueSet = new Set(filterValue);

  return rows.filter((row) => {
    const key: string = row.values[columnId];
    const keyParts = key.split(".");
    return keyParts.some((_, tailIndex) =>
      filterValueSet.has(keyParts.slice(0, tailIndex + 1).join("."))
    );
  });
};

export type TreeNode = {
  label: string;
  value: string;
  children: TreeNode[];
};

export const transformCategoriesToNodes = (
  categoryKeys: string[],
  categoriesMap: Map<string, { name?: string }> = new Map()
): TreeNode[] => {
  const keyToNode = new Map<string, TreeNode>();

  // The empty string is a dummy root of every sub-key.
  keyToNode.set("", {
    label: "",
    value: "",
    children: [],
  });

  categoryKeys.forEach((key) => {
    const keyParts = key.split(".");

    // For every sub-key of the category, create an intermediate parent. At the last step of the
    // loop the `childKey` is equal to `key` and the parent is guaranteed to exist.
    keyParts.forEach((tail, tailIndex) => {
      const parentKey = keyParts.slice(0, tailIndex).join(".");
      const childKey = keyParts.slice(0, tailIndex + 1).join(".");

      if (keyToNode.has(childKey)) {
        // There may be duplicate categories and/or intermediate parents.
        return;
      }

      const child: TreeNode = {
        label: categoriesMap.get(childKey)?.name ?? tail,
        value: childKey,
        children: [],
      };
      keyToNode.set(childKey, child);

      // This should always exist by this point.
      const parent = keyToNode.get(parentKey);
      if (parent) {
        parent.children.push(child);
      }
    });
  });

  return keyToNode.get("")?.children ?? [];
};

export const useCheckboxTreeFilter = <D extends Record<string, unknown>>({
  id,
  filterValue,
  preFilteredRows,
  setFilter,
}: Omit<ColumnInstance<D>, "filterValue"> & {
  filterValue?: string[];
}) => {
  const categoriesMap = useSelector(selectDataCategoriesMap);

  const nodes = React.useMemo(() => {
    const columnValues = new Set<string>();
    preFilteredRows.forEach((row) => {
      columnValues.add(row.values[id]);
    });
    return transformCategoriesToNodes(Array.from(columnValues), categoriesMap);
  }, [preFilteredRows, categoriesMap, id]);

  // All roots are selected by default.
  const initialSelected = React.useMemo(
    () => nodes.map((node) => node.value),
    [nodes]
  );

  const onChangeSelected = React.useCallback(
    (newSelected: string[] | undefined) => {
      setFilter(newSelected);
    },
    [setFilter]
  );

  return {
    selected: filterValue ?? initialSelected,
    nodes,
    onChangeSelected,
  };
};
