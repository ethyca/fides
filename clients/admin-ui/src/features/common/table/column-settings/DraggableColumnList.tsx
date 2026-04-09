import { Flex } from "fidesui";
import produce from "immer";
import { useCallback, useEffect, useState } from "react";

import { DraggableColumnListItem } from "./DraggableColumnListItem";

export type DraggableColumn = {
  id: string;
  isVisible: boolean;
  displayText: string;
};

type EditableColumns = {
  columns: DraggableColumn[];
  moveColumn: (dragIndex: number, hoverIndex: number) => void;
  setColumnVisible: (index: number, isVisible: boolean) => void;
};

export const useEditableColumns = ({
  columns: initialColumns,
}: {
  columns: DraggableColumn[];
}): EditableColumns => {
  const [columns, setColumns] = useState<DraggableColumn[]>(
    initialColumns ?? [],
  );

  useEffect(() => {
    setColumns(
      initialColumns?.map((c) => ({
        ...c,
      })) || [],
    );
  }, [initialColumns]);

  const moveColumn = useCallback((dragIndex: number, hoverIndex: number) => {
    setColumns((prev: DraggableColumn[]) =>
      produce(prev, (draft) => {
        const dragged = draft[dragIndex];
        draft.splice(dragIndex, 1);
        draft.splice(hoverIndex, 0, dragged);
      }),
    );
  }, []);

  const setColumnVisible = useCallback((index: number, isVisible: boolean) => {
    setColumns((prev: DraggableColumn[]) =>
      produce(prev, (draft) => {
        if (draft[index]) {
          draft[index].isVisible = isVisible;
        }
      }),
    );
  }, []);

  return {
    columns,
    moveColumn,
    setColumnVisible,
  };
};

type DraggableColumnListProps = {
  columns: DraggableColumn[];
  columnEditor: EditableColumns;
};

export const DraggableColumnList = ({
  columns,
  columnEditor,
}: DraggableColumnListProps) => (
  <Flex vertical className="w-full">
    {columns.map((column, index) => (
      <DraggableColumnListItem
        id={column.id}
        index={index}
        isVisible={column.isVisible}
        key={column.id}
        moveColumn={columnEditor.moveColumn}
        setColumnVisible={columnEditor.setColumnVisible}
        text={column.displayText}
      />
    ))}
  </Flex>
);
