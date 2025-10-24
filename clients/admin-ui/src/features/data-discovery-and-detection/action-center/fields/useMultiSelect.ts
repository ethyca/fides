import _ from "lodash";
import { useState } from "react";

type MultiSelectMode = "inclusive" | "exclusive";

interface ListItem {
  itemKey: React.Key;
}

/** TODO: Rename this to something better */
export const useMultiSelect = <T extends ListItem>() => {
  const [mode, setMode] = useState<MultiSelectMode>("inclusive");
  const [listItems, setListItemsState] = useState<Array<T>>([]);
  const [selected, setSelectedState] = useState<React.Key[]>([]);

  const extractKeys = (data: Array<T>) => data.map(({ itemKey }) => itemKey);

  /** considering using sets or just a better method of keeping unique */
  const setSelected = (newSelected: Array<React.Key>) => {
    setSelectedState(_.uniq(newSelected));
  };

  const setListItems = (newListItems: Array<T>) => {
    setListItemsState(_.uniqBy(newListItems, "itemKey"));
  };

  const updateListItems = (newListItems: Array<T>) => {
    /** there should be a better way of doing this other than switch statements */
    switch (mode) {
      case "inclusive":
        setListItems([...listItems, ...newListItems]);
        break;
      default:
        setListItems([...listItems, ...newListItems]);
        setSelected([...selected, ...extractKeys(newListItems)]);
        break;
    }
  };

  const updateSelected = (itemKey: React.Key, isSelected: boolean) => {
    switch (isSelected) {
      case true:
        setSelected([...selected, itemKey]);
        break;
      default:
        setSelected(selected.filter((k) => k !== itemKey));
        break;
    }
  };

  const updateMode = (newMode: MultiSelectMode) => {
    setMode(newMode);
    switch (newMode) {
      case "inclusive":
        setSelected([]);
        break;
      default:
        setSelected(extractKeys(listItems));
        break;
    }
  };

  const selectAll = (isSelected: boolean) => {
    switch (isSelected) {
      case true:
        setSelected(extractKeys(listItems));
        break;
      default:
        setMode("inclusive");
        setSelected([]);
        break;
    }
  };

  const reset = () => {
    setSelected([]);
    setListItems([]);
  };

  const excluded = listItems.flatMap((item) =>
    !selected.find((key) => key === item.itemKey) ? [item] : [],
  );

  return {
    mode,
    updateMode,
    updateListItems,
    updateSelected,
    selectAll,
    allSelected:
      mode === "inclusive"
        ? selected.length > 0 && listItems.length === selected.length
        : excluded.length === 0,
    indeterminate:
      mode === "inclusive"
        ? selected.length > 0 && listItems.length !== selected.length
        : excluded.length > 0,
    selected,
    selectedItems: listItems.flatMap((item) =>
      selected.find((key) => key === item.itemKey) ? [item] : [],
    ),
    excluded,
    reset,
  };
};
