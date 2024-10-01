import type { Identifier, XYCoord } from "dnd-core";
import {
  AntSwitch as Switch,
  Box,
  FormControl,
  FormLabel,
  GripDotsVerticalIcon,
  List,
  ListIcon,
  ListItem,
} from "fidesui";
import produce from "immer";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useDrag, useDrop } from "react-dnd";

export const ItemTypes = {
  DraggableColumnListItem: "DraggableColumnListItem",
};

type DragItem = {
  index: number;
  id: number;
  type: string;
};

type DraggableColumnListItemProps = {
  index: number;
  id: string;
  isVisible: boolean;
  text: string;
  moveColumn: (hoverIndex: number, dragIndex: number) => void;
  setColumnVisible: (column: number, isVisible: boolean) => void;
};

const useDraggableColumnListItem = ({
  id,
  index,
  moveColumn,
  setColumnVisible,
}: Pick<
  DraggableColumnListItemProps,
  "id" | "index" | "moveColumn" | "setColumnVisible"
>) => {
  const ref = useRef<HTMLDivElement>(null);
  const [{ handlerId }, drop] = useDrop<
    DragItem,
    void,
    { handlerId: Identifier | null }
  >({
    accept: ItemTypes.DraggableColumnListItem,
    collect(monitor) {
      return {
        handlerId: monitor.getHandlerId(),
      };
    },
    hover(item: DragItem, monitor) {
      if (!ref.current) {
        return;
      }
      const dragIndex = item.index;
      const hoverIndex = index;

      // Don't replace items with themselves
      if (dragIndex === hoverIndex) {
        return;
      }

      // Determine rectangle on screen
      const hoverBoundingRect = ref.current?.getBoundingClientRect();

      // Get vertical middle
      const hoverMiddleY =
        (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;

      // Determine mouse position
      const clientOffset = monitor.getClientOffset();

      // Get pixels to the top
      const hoverClientY = (clientOffset as XYCoord).y - hoverBoundingRect.top;

      // Only perform the move when the mouse has crossed half of the item's
      // height
      // When dragging downwards, only move when the cursor is below 50%
      // When dragging upwards, only move when the cursor is above 50%

      // Dragging downwards
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }

      // Dragging upwards
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }

      // Time to actually perform the action
      moveColumn(dragIndex, hoverIndex);

      // Note: we're mutating the monitor item here!
      // Generally it's better to avoid mutations,
      // but it's good here for the sake of performance
      // to avoid expensive index searches.
      Object.assign(item, { index: hoverIndex });
    },
  });

  const [{ isDragging }, drag, preview] = useDrag({
    type: ItemTypes.DraggableColumnListItem,
    item: () => ({ id, index }),
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  });

  drag(drop(ref));

  const handleColumnVisibleToggle = (checked: boolean) => {
    setColumnVisible(index, checked);
  };

  return { isDragging, ref, handlerId, preview, handleColumnVisibleToggle };
};

const DraggableColumnListItem = ({
  id,
  index,
  isVisible,
  moveColumn,
  setColumnVisible,
  text,
}: DraggableColumnListItemProps) => {
  const { ref, isDragging, handlerId, preview, handleColumnVisibleToggle } =
    useDraggableColumnListItem({
      index,
      id,
      moveColumn,
      setColumnVisible,
    });

  return (
    <ListItem
      alignItems="center"
      display="flex"
      minWidth={0}
      ref={(element) => {
        preview(element);
      }}
      data-handler-id={handlerId}
      opacity={isDragging ? 0.2 : 1}
    >
      <Box ref={ref} cursor={isDragging ? "grabbing" : "grab"}>
        <ListIcon
          as={GripDotsVerticalIcon}
          color="gray.300"
          flexShrink={0}
          height="20px"
          width="20px"
          _hover={{
            color: "gray.700",
          }}
        />
      </Box>
      <FormControl alignItems="center" display="flex" minWidth={0} title={text}>
        <FormLabel
          color="gray.700"
          fontSize="normal"
          fontWeight={400}
          htmlFor={`${id}`}
          mb="0"
          minWidth={0}
          overflow="hidden"
          textOverflow="ellipsis"
          whiteSpace="nowrap"
          flexGrow={1}
        >
          {text}
        </FormLabel>
        <Switch
          id={`${id}`}
          checked={isVisible}
          onChange={handleColumnVisibleToggle}
        />
      </FormControl>
    </ListItem>
  );
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

export type DraggableColumn = {
  id: string;
  isVisible: boolean;
  displayText: string;
};

type DraggableColumnListProps = {
  columns: DraggableColumn[];
  columnEditor: EditableColumns;
};

export const DraggableColumnList = ({
  columns,
  columnEditor,
}: DraggableColumnListProps) => (
  <List spacing={4}>
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
  </List>
);
