import {
  AntButton as Button,
  Box,
  Checkbox,
  FilterIcon,
  GreenCircleIcon,
  IconButton,
  Menu,
  MenuButton,
  MenuDivider,
  MenuItem,
  MenuList,
  Portal,
} from "fidesui";
import { useMemo } from "react";

export interface FieldValueToIsSelected {
  [fieldValue: string]: boolean;
}

interface Props {
  filterValue: FieldValueToIsSelected;
  onClearFilterOptions: () => void;
  onToggleFilterOption: (option: string | number, isSelected: boolean) => void;
  options: string[];
}

const FilterMenu = ({
  filterValue,
  onClearFilterOptions,
  onToggleFilterOption,
  options,
}: Props) => {
  const hasActiveFilter = useMemo(() => {
    if (!Object.values(filterValue).every((value) => value)) {
      return true;
    }
    return false;
  }, [filterValue]);

  return (
    <Menu isLazy closeOnSelect={false}>
      {({ onClose }) => (
        <>
          <MenuButton
            as={IconButton}
            icon={<FilterIcon width="16px" height="16px" />}
            size="sm"
            variant="ghost"
            aria-label="Column filters"
          />
          {hasActiveFilter ? (
            <GreenCircleIcon
              border="2px"
              borderColor="white"
              borderRadius="50px"
              bottom="5px"
              h={2.5}
              position="relative"
              right="12px"
              w={2.5}
            />
          ) : null}

          <Portal>
            <MenuList boxShadow="base">
              <Box display="flex" justifyContent="space-between" px={2}>
                <Button size="small" onClick={() => onClearFilterOptions()}>
                  Clear
                </Button>
                <Button type="primary" size="small" onClick={onClose}>
                  Done
                </Button>
              </Box>
              <MenuDivider />
              {options.map((option) => (
                <MenuItem
                  as={Checkbox}
                  value={option}
                  key={option}
                  isChecked={filterValue[option] ?? false}
                  onChange={({ target }) => {
                    onToggleFilterOption(
                      option,
                      (target as HTMLInputElement).checked,
                    );
                  }}
                  _focusWithin={{
                    bg: "gray.100",
                  }}
                  colorScheme="complimentary"
                >
                  {option}
                </MenuItem>
              ))}
            </MenuList>
          </Portal>
        </>
      )}
    </Menu>
  );
};

export default FilterMenu;
