import { Table as TableInstance } from "@tanstack/react-table";
import {
  AntButton as Button,
  AntFlex,
  Box,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
} from "fidesui";
import { useCallback, useMemo } from "react";

import { getColumnHeaderText } from "../util";
import {
  DraggableColumn,
  DraggableColumnList,
  useEditableColumns,
} from "./DraggableColumnList";

type ColumnSettingsModalProps<T> = {
  isOpen: boolean;
  onClose: () => void;
  headerText: string;
  columnNameMap: Record<string, string>;
  prefixColumns: string[];
  tableInstance: TableInstance<T>;
  savedCustomReportId: string;
  onColumnOrderChange: (columns: string[]) => void;
  onColumnVisibilityChange: (columnVisibility: Record<string, boolean>) => void;
};

export const ColumnSettingsModal = <T,>({
  isOpen,
  onClose,
  headerText,
  tableInstance,
  columnNameMap,
  prefixColumns,
  savedCustomReportId,
  onColumnOrderChange,
  onColumnVisibilityChange,
}: ColumnSettingsModalProps<T>) => {
  const initialColumns = useMemo(
    () =>
      tableInstance
        .getAllColumns()
        .filter((c) => !prefixColumns.includes(c.id))
        .map((c) => ({
          id: c.id,
          displayText: getColumnHeaderText({
            columnNameMap,
            columnId: c.id,
          }),
          isVisible:
            tableInstance.getState().columnVisibility[c.id] ?? c.getIsVisible(),
        }))
        .sort((a, b) => {
          // columnOrder is not always a complete list. Sorts by columnOrder but leaves the rest alone
          const { columnOrder } = tableInstance.getState();
          const aIndex = columnOrder.indexOf(a.id);
          const bIndex = columnOrder.indexOf(b.id);
          if (aIndex === -1 && bIndex === -1) {
            return 0;
          }
          if (aIndex === -1) {
            return 1;
          }
          if (bIndex === -1) {
            return -1;
          }
          return aIndex - bIndex;
        }),
    // watch savedCustomReportId so that when a saved report is loaded, we can update these column definitions to match
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [savedCustomReportId, columnNameMap],
  );
  const columnEditor = useEditableColumns({
    columns: initialColumns,
  });

  const handleSave = useCallback(() => {
    const newColumnOrder: string[] = [
      ...prefixColumns,
      ...columnEditor.columns.map((c) => c.id),
    ];
    const newColumnVisibility = columnEditor.columns.reduce(
      (acc: Record<string, boolean>, current: DraggableColumn) => {
        // eslint-disable-next-line no-param-reassign
        acc[current.id] = current.isVisible;
        return acc;
      },
      {},
    );
    onColumnOrderChange(newColumnOrder);
    onColumnVisibilityChange(newColumnVisibility);
    onClose();
  }, [
    onClose,
    prefixColumns,
    columnEditor.columns,
    onColumnOrderChange,
    onColumnVisibilityChange,
  ]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} isCentered size="2xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader pb={0}>{headerText}</ModalHeader>
        <ModalCloseButton data-testid="column-settings-close-button" />
        <ModalBody>
          <Text fontSize="sm" color="gray.500" mb={4}>
            You can toggle columns on and off to hide or show them in the table.
            Additionally, you can drag columns up or down to change the order
          </Text>
          <AntFlex className="max-h-96 overflow-y-auto">
            <DraggableColumnList
              columns={columnEditor.columns}
              columnEditor={columnEditor}
            />
          </AntFlex>
        </ModalBody>
        <ModalFooter>
          <Box display="flex" justifyContent="space-between" width="100%">
            <Button onClick={onClose} className="mr-3 grow">
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              type="primary"
              className="grow"
              data-testid="save-button"
            >
              Save
            </Button>
          </Box>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
