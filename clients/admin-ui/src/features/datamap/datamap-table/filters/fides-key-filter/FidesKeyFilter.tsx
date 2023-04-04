import {
  Box,
  Button,
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
} from '@fidesui/react';
import { ColumnInstance } from 'react-table';

import { DatamapRow } from '../../../datamap.slice';
import { useFidesKeyFilter } from './helpers';

interface Props {
  column: ColumnInstance<DatamapRow>;
}

const FidesKeyFilter = ({ column }: Props) => {
  const { options, selectedSet, toggle, clear } = useFidesKeyFilter(column);

  const hasActiveFilter = selectedSet.size !== options.length;

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
                <Button variant="outline" size="xs" onClick={() => clear()}>
                  Clear
                </Button>
                <Button colorScheme="primary" size="xs" onClick={onClose}>
                  Done
                </Button>
              </Box>
              <MenuDivider />
              {options.map((fidesKey) => (
                <MenuItem
                  as={Checkbox}
                  value={fidesKey}
                  key={fidesKey}
                  isChecked={selectedSet.has(fidesKey)}
                  onChange={({ target }) =>
                    toggle(fidesKey, (target as HTMLInputElement).checked)
                  }
                  _focusWithin={{
                    bg: 'gray.100',
                  }}
                  colorScheme="complimentary"
                >
                  {fidesKey}
                </MenuItem>
              ))}
            </MenuList>
          </Portal>
        </>
      )}
    </Menu>
  );
};

export default FidesKeyFilter;
