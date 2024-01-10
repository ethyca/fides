import {
  Box,
  Button,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
} from "@fidesui/react";
import { Table as TableInstance } from "@tanstack/react-table";
import { useCallback, useMemo } from "react";

import {
  DraggableColumn,
  DraggableColumnList,
  useEditableColumns,
} from "./DraggableColumnList";

type ColumnSettingsModalProps<T> = {
  isOpen: boolean;
  onClose: () => void;
  prefixColumns: string[];
  tableInstance: TableInstance<T>;
};

export const ColumnSettingsModal = <T,>({
  isOpen,
  onClose,
  tableInstance,
  prefixColumns,
}: ColumnSettingsModalProps<T>) => {
  const initialColumns = useMemo(
    () =>
      tableInstance
        .getAllColumns()
        .filter((c) => !prefixColumns.includes(c.id))
        .map((c) => ({
          id: c.id,
          displayText: c.columnDef?.meta?.displayText || c.id,
          isVisible: c.getIsVisible(),
        })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );
  const columnEditor = useEditableColumns({
    columns: initialColumns,
  });

  const handleSave = useCallback(() => {
    tableInstance.setColumnOrder([
      ...prefixColumns,
      ...columnEditor.columns.map((c) => c.id),
    ]);
    tableInstance.setColumnVisibility(
      columnEditor.columns.reduce(
        (acc: Record<string, boolean>, current: DraggableColumn) => {
          // eslint-disable-next-line no-param-reassign
          acc[current.id] = current.isVisible;
          return acc;
        },
        {}
      )
    );
    onClose();
  }, [onClose, prefixColumns, tableInstance, columnEditor.columns]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader pb={0}>Data Map Settings</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Text fontSize="sm" color="gray.500" mb={2}>
            You can toggle columns on and off to hide or show them in the table.
            Additionally, you can drag columns up or down to change the order
          </Text>
          <Tabs colorScheme="complimentary">
            <TabList>
              <Tab color="complimentary.500">Columns</Tab>
            </TabList>
            <TabPanels>
              <TabPanel p={0} pt={4} maxHeight="270px" overflowY="scroll">
                <DraggableColumnList
                  columns={columnEditor.columns}
                  columnEditor={columnEditor}
                />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>
        <ModalFooter>
          <Box display="flex" justifyContent="space-between" width="100%">
            <Button
              variant="outline"
              size="sm"
              mr={3}
              onClick={onClose}
              flexGrow={1}
            >
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              size="sm"
              onClick={handleSave}
              flexGrow={1}
            >
              Save
            </Button>
          </Box>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
