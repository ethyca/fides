import {
  closestCenter,
  DndContext,
  DragEndEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Flex } from "fidesui";
import produce from "immer";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DraggableColumnListItem } from "./DraggableColumnListItem";

export type DraggableColumn = {
  id: string;
  isVisible: boolean;
  displayText: string;
};

type EditableColumns = {
  columns: DraggableColumn[];
  moveColumn: (activeId: string, overId: string) => void;
  setColumnVisible: (id: string, isVisible: boolean) => void;
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

  const moveColumn = useCallback((activeId: string, overId: string) => {
    setColumns((prev: DraggableColumn[]) => {
      const oldIndex = prev.findIndex((c) => c.id === activeId);
      const newIndex = prev.findIndex((c) => c.id === overId);
      if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) {
        return prev;
      }
      return arrayMove(prev, oldIndex, newIndex);
    });
  }, []);

  const setColumnVisible = useCallback((id: string, isVisible: boolean) => {
    setColumns((prev: DraggableColumn[]) =>
      produce(prev, (draft) => {
        const target = draft.find((c) => c.id === id);
        if (target) {
          target.isVisible = isVisible;
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
}: DraggableColumnListProps) => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const items = useMemo(() => columns.map((c) => c.id), [columns]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) {
      return;
    }
    columnEditor.moveColumn(String(active.id), String(over.id));
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        <Flex vertical className="w-full">
          {columns.map((column) => (
            <DraggableColumnListItem
              id={column.id}
              isVisible={column.isVisible}
              key={column.id}
              setColumnVisible={columnEditor.setColumnVisible}
              text={column.displayText}
            />
          ))}
        </Flex>
      </SortableContext>
    </DndContext>
  );
};
