import { Button, Flex, Modal, Paragraph } from "fidesui";
import { useCallback, useMemo } from "react";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";

import { getColumnHeaderText } from "../v2/util";
import {
  DraggableColumn,
  DraggableColumnList,
  useEditableColumns,
} from "./DraggableColumnList";

type ColumnSettingsModalProps = {
  isOpen: boolean;
  onClose: () => void;
  headerText: string;
  columnNameMap: Record<string, string>;
  prefixColumns: string[];
  columns: Pick<DraggableColumn, "id" | "isVisible">[];
  savedCustomReportId: string;
  onColumnOrderChange: (columns: string[]) => void;
  onColumnVisibilityChange: (columnVisibility: Record<string, boolean>) => void;
};

export const ColumnSettingsModal = ({
  isOpen,
  onClose,
  headerText,
  columnNameMap,
  prefixColumns,
  columns,
  savedCustomReportId,
  onColumnOrderChange,
  onColumnVisibilityChange,
}: ColumnSettingsModalProps) => {
  const initialColumns = useMemo(
    () =>
      columns
        .filter((c) => !prefixColumns.includes(c.id))
        .map((c) => ({
          id: c.id,
          displayText: getColumnHeaderText({
            columnNameMap,
            columnId: c.id,
          }),
          isVisible: c.isVisible,
        })),
    // watch savedCustomReportId so that when a saved report is loaded, we can update these column definitions to match
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [savedCustomReportId, columnNameMap, columns, prefixColumns],
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
    <Modal
      open={isOpen}
      onCancel={onClose}
      width={MODAL_SIZE.md}
      centered
      destroyOnHidden
      title={headerText}
      footer={
        <Flex justify="flex-end" gap="small">
          <Button onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} type="primary" data-testid="save-button">
            Save
          </Button>
        </Flex>
      }
    >
      <Paragraph type="secondary">
        You can toggle columns on and off to hide or show them in the table.
        Additionally, you can drag columns up or down to change the order
      </Paragraph>
      <Flex className="max-h-96 overflow-y-auto pr-3">
        <DraggableColumnList
          columns={columnEditor.columns}
          columnEditor={columnEditor}
        />
      </Flex>
    </Modal>
  );
};
