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
  initialAllSelected?: boolean;
  itemCount: number;
  selected: string[];
  onChange: (newSelected: string[]) => void;
}

export const usePaginatedPicker = ({
  initialAllSelected,
  itemCount,
  selected,
  onChange,
}: UsePaginatedPickerProps) => {
  const [allSelected, setAllSelected] = useState(
    initialAllSelected || selected.length === itemCount
  );

  const someSelected = !!selected.length;

  const handleToggleSelection = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      const newSelected = [...selected, id];
      onChange(newSelected);
      if (newSelected.length === itemCount) {
        setAllSelected(true);
      }
    }
  };

  const handleToggleAll = () => {
    onChange([]);
    setAllSelected(!allSelected);
  };

  return {
    allSelected,
    someSelected,
    handleToggleAll,
    handleToggleSelection,
  };
};
