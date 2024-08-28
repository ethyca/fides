import { useState } from "react";

export const NUM_TO_SHOW = 5;

interface PickerItem {
  id: string;
  name: string;
}

interface UsePickerProps<T extends PickerItem> {
  items: T[];
  selected: string[];
  onChange: (newSelected: string[]) => void;
}

export const usePicker = <T extends { id: string; name: string }>({
  items,
  selected,
  onChange,
}: UsePickerProps<T>) => {
  const allSelected =
    items.every((item) => selected.includes(item.id)) && !!items.length;
  const someSelected =
    items.some((item) => selected.includes(item.id)) && !!items.length;

  const handleToggleSelection = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const handleToggleAll = () => {
    if (allSelected) {
      onChange([]);
    } else {
      onChange(items.map((i) => i.id));
    }
  };

  return {
    allSelected,
    someSelected,
    handleToggleAll,
    handleToggleSelection,
  };
};

interface UsePaginatedPickerProps {
  initialSelected: string[];
  initialExcluded: string[];
  initialAllSelected?: boolean;
  itemCount: number | null;
}

export const usePaginatedPicker = ({
  initialSelected,
  initialExcluded,
  initialAllSelected,
  itemCount,
}: UsePaginatedPickerProps) => {
  const [selectedItems, setSelectedItems] = useState(initialSelected);
  const [excludedItems, setExcludedItems] = useState(initialExcluded);

  // allSelected needs to be tracked separately from selectedItems because
  // [] represents an "all selected" state when editing but an empty state
  // when creating
  const [allSelected, setAllSelected] = useState(
    initialAllSelected || selectedItems.length === itemCount,
  );

  const someSelected = !!selectedItems.length || !!excludedItems.length;

  const handleToggleItemSelected = (id: string) => {
    if (allSelected) {
      const newExcluded = excludedItems.includes(id)
        ? excludedItems.filter((s) => s !== id)
        : [...excludedItems, id];
      setExcludedItems(newExcluded);
    } else {
      const newSelected = selectedItems.includes(id)
        ? selectedItems.filter((s) => s !== id)
        : [...selectedItems, id];
      setSelectedItems(newSelected);
      if (newSelected.length === itemCount) {
        setAllSelected(true);
      }
    }
  };

  const handleToggleAll = () => {
    if (allSelected) {
      setExcludedItems([]);
      if (!excludedItems.length) {
        setAllSelected(false);
      }
    } else {
      setSelectedItems([]);
      setAllSelected(true);
    }
  };

  return {
    selected: selectedItems,
    excluded: excludedItems,
    allSelected,
    someSelected,
    handleToggleAll,
    handleToggleItemSelected,
  };
};
