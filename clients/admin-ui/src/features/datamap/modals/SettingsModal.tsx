import {
  Box,
  Button,
  FormControl,
  FormLabel,
  GripDotsVerticalIcon,
  List,
  ListIcon,
  ListItem,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Switch,
  Tab,
  TabList,
  TabPanel,
  TabPanels,
  Tabs,
  Text,
} from '@fidesui/react';
import type { Identifier, XYCoord } from 'dnd-core';
import produce from 'immer';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useDrag, useDrop } from 'react-dnd';
import { useDispatch } from 'react-redux';

import { useAppSelector } from '~/app/hooks';

import { ItemTypes, SYSTEM_NAME } from '../constants';
import {
  DatamapColumn,
  selectColumns,
  setColumns as setTableColumns,
} from '../datamap.slice';

interface DragItem {
  index: number;
  id: number;
  type: string;
}

interface DraggableColumnListItemProps {
  index: number;
  id: number;
  isVisible: boolean;
  text: string;
  moveColumn: (hoverIndex: number, dragIndex: number) => void;
  setColumnVisible: (column: number, isVisible: boolean) => void;
}

const useDraggableColumnListItem = ({
  id,
  index,
  moveColumn,
  setColumnVisible,
}: Pick<
  DraggableColumnListItemProps,
  'id' | 'index' | 'moveColumn' | 'setColumnVisible'
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

  const handleColumnVisibleToggle = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setColumnVisible(index, event.target.checked);
  };

  return { isDragging, ref, handlerId, preview, handleColumnVisibleToggle };
};

const DraggableColumnListItem: React.FC<DraggableColumnListItemProps> = ({
  id,
  index,
  isVisible,
  moveColumn,
  setColumnVisible,
  text,
}) => {
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
      ref={preview}
      data-handler-id={handlerId}
      opacity={isDragging ? 0.2 : 1}
    >
      <Box ref={ref} cursor={isDragging ? 'grabbing' : 'grab'}>
        <ListIcon
          as={GripDotsVerticalIcon}
          color="gray.300"
          flexShrink={0}
          height="20px"
          width="20px"
          _hover={{
            color: 'gray.700',
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
          colorScheme="complimentary"
          id={`${id}`}
          mr={2}
          isChecked={isVisible}
          onChange={handleColumnVisibleToggle}
        />
      </FormControl>
    </ListItem>
  );
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const useEditableColumns = <T extends DatamapColumn>({
  columns: initialColumns,
}: {
  columns?: T[];
}) => {
  const [columns, setColumns] = useState<T[]>(initialColumns ?? []);

  useEffect(() => {
    setColumns(
      initialColumns?.map((c) => ({
        ...c,
      })) || []
    );
  }, [initialColumns]);

  const moveColumn = useCallback((dragIndex: number, hoverIndex: number) => {
    setColumns((prev: T[]) =>
      produce(prev, (draft) => {
        const dragged = draft[dragIndex];
        draft.splice(dragIndex, 1);
        draft.splice(hoverIndex, 0, dragged);
      })
    );
  }, []);

  const setColumnVisible = useCallback((index: number, isVisible: boolean) => {
    setColumns((prev: T[]) =>
      produce(prev, (draft) => {
        if (draft[index]) {
          draft[index].isVisible = isVisible;
        }
      })
    );
  }, []);

  return {
    columns,
    moveColumn,
    setColumnVisible,
  };
};

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const dispatch = useDispatch();
  const tableColumns = useAppSelector(selectColumns);

  const tableEditor = useEditableColumns<DatamapColumn>({
    columns: tableColumns,
  });

  const handleSave = useCallback(() => {
    dispatch(setTableColumns(tableEditor.columns));
    onClose();
  }, [onClose, dispatch, tableEditor.columns]);

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
                <List spacing={4}>
                  {tableEditor.columns
                    .filter((c) => c.value !== SYSTEM_NAME)
                    .map((column, index) => (
                      <DraggableColumnListItem
                        id={column.id}
                        index={index + 1}
                        isVisible={column.isVisible}
                        key={column.id}
                        moveColumn={tableEditor.moveColumn}
                        setColumnVisible={tableEditor.setColumnVisible}
                        text={column.text}
                      />
                    ))}
                </List>
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

export default SettingsModal;
