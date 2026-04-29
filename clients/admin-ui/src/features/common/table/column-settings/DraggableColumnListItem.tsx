import type { Identifier, XYCoord } from "dnd-core";
import { Flex, Icons, Switch } from "fidesui";
import React, { useRef } from "react";
import { useDrag, useDrop } from "react-dnd";

const ITEM_TYPE = "DraggableColumnListItem";

type DragItem = {
  index: number;
  id: string;
  type: string;
};

type DraggableColumnListItemProps = {
  index: number;
  id: string;
  isVisible: boolean;
  text: string;
  moveColumn: (dragIndex: number, hoverIndex: number) => void;
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
  // rowRef is the drop target (the full row, so hover triggers anywhere on it).
  // dragRef is the drag source (the drag handle icon only).
  const rowRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<HTMLDivElement>(null);

  const [{ handlerId }, drop] = useDrop<
    DragItem,
    void,
    { handlerId: Identifier | null }
  >({
    accept: ITEM_TYPE,
    collect(monitor) {
      return {
        handlerId: monitor.getHandlerId(),
      };
    },
    hover(item: DragItem, monitor) {
      if (!rowRef.current) {
        return;
      }
      const dragIndex = item.index;
      const hoverIndex = index;

      if (dragIndex === hoverIndex) {
        return;
      }

      const hoverBoundingRect = rowRef.current?.getBoundingClientRect();
      const hoverMiddleY =
        (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;
      const clientOffset = monitor.getClientOffset();
      const hoverClientY = (clientOffset as XYCoord).y - hoverBoundingRect.top;

      // Only move when the mouse has crossed half of the item's height
      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }

      moveColumn(dragIndex, hoverIndex);
      // Mutating the monitor item for performance (avoids expensive index searches)
      Object.assign(item, { index: hoverIndex });
    },
  });

  const [{ isDragging }, drag, preview] = useDrag({
    type: ITEM_TYPE,
    item: () => ({ id, index }),
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  });

  drop(rowRef);
  drag(dragRef);
  preview(rowRef);

  const handleColumnVisibleToggle = (checked: boolean) => {
    setColumnVisible(index, checked);
  };

  return {
    isDragging,
    rowRef,
    dragRef,
    handlerId,
    handleColumnVisibleToggle,
  };
};

export const DraggableColumnListItem = ({
  id,
  index,
  isVisible,
  moveColumn,
  setColumnVisible,
  text,
}: DraggableColumnListItemProps) => {
  const { rowRef, dragRef, isDragging, handlerId, handleColumnVisibleToggle } =
    useDraggableColumnListItem({
      index,
      id,
      moveColumn,
      setColumnVisible,
    });

  return (
    <Flex
      align="center"
      ref={rowRef}
      data-handler-id={handlerId}
      style={{ opacity: isDragging ? 0.2 : 1 }}
      data-testid={`column-list-item-${id}`}
      gap="small"
      className="py-1" // use padding instead of parent flex gap to better support dragging
    >
      <div
        ref={dragRef}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
        className="-ml-1 shrink-0"
        data-testid={`column-dragger-${id}`}
      >
        <Icons.Draggable size={20} color="var(--ant-neutral-400)" />
      </div>
      <Flex align="center" className="min-w-0 flex-1" title={text}>
        <label htmlFor={id} className="mb-0 min-w-0 flex-1 truncate text-sm">
          {text}
        </label>
        <Switch
          id={id}
          size="small"
          checked={isVisible}
          onChange={handleColumnVisibleToggle}
        />
      </Flex>
    </Flex>
  );
};
