import { AddIcon, DeleteIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  ChakraProps,
  DragHandleIcon,
  Flex,
  IconButton,
  List,
  Text,
} from "@fidesui/react";
import { Select } from "chakra-react-select";
import { motion, Reorder, useDragControls } from "framer-motion";
import { useState } from "react";

import { Label, Option, SELECT_STYLES } from "~/features/common/form/inputs";
import QuestionTooltip from "~/features/common/QuestionTooltip";

const ScrollableListItem = <T extends unknown>({
  item,
  label,
  draggable,
  onDeleteItem,
  onRowClick,
  maxH = 10,
}: {
  item: T;
  label: string;
  draggable?: boolean;
  onDeleteItem?: (item: T) => void;
  onRowClick?: (item: T) => void;
  maxH?: number;
}) => {
  const dragControls = useDragControls();

  return (
    <Reorder.Item value={item} dragListener={false} dragControls={dragControls}>
      <Flex
        direction="row"
        gap={2}
        maxH={maxH}
        px={2}
        align="center"
        role="group"
        borderY="1px"
        my="-1px"
        borderColor="gray.200"
        _hover={onRowClick ? { bgColor: "gray.100" } : undefined}
        bgColor="white"
      >
        {draggable ? (
          <DragHandleIcon
            onPointerDown={(e) => dragControls.start(e)}
            cursor="grab"
          />
        ) : null}
        <Flex
          direction="row"
          gap={2}
          p={2}
          align="center"
          w="full"
          cursor={onRowClick ? "pointer" : "auto"}
          onClick={() => {
            if (onRowClick) {
              onRowClick(item);
            }
          }}
        >
          <Text fontSize="sm" userSelect="none">
            {label}
          </Text>
        </Flex>

        {onDeleteItem ? (
          <IconButton
            aria-label="Delete"
            onClick={() => onDeleteItem(item)}
            icon={<DeleteIcon />}
            size="xs"
            variant="outline"
            bgColor="white"
            visibility="hidden"
            alignSelf="end"
            mb={2}
            _groupHover={{ visibility: "visible" }}
          />
        ) : null}
      </Flex>
    </Reorder.Item>
  );
};

const ScrollableListAdd = ({
  label,
  options,
  onOptionSelected,
}: {
  label: string;
  options: Option[];
  onOptionSelected: (opt: Option) => void;
}) => {
  const [isAdding, setIsAdding] = useState<boolean>(false);
  const [selectValue, setSelectValue] = useState<Option | undefined>(undefined);

  const handleElementSelected = (event: any) => {
    onOptionSelected(event);
    setIsAdding(false);
    setSelectValue(undefined);
  };

  return isAdding ? (
    <Box w="full">
      <Select
        chakraStyles={SELECT_STYLES}
        size="sm"
        value={selectValue}
        options={options}
        onChange={(e: any) => handleElementSelected(e)}
        autoFocus
        menuPosition="fixed"
        menuPlacement="auto"
      />
    </Box>
  ) : (
    <Button
      onClick={() => setIsAdding(true)}
      w="full"
      size="sm"
      variant="outline"
      rightIcon={<AddIcon boxSize={3} />}
    >
      {label}
    </Button>
  );
};

const ScrollableList = <T extends unknown>({
  label,
  tooltip,
  draggable,
  addButtonLabel,
  allItems,
  idField,
  nameField = idField,
  values,
  setValues,
  canDeleteItem,
  onRowClick,
  selectOnAdd,
  getItemLabel,
  createNewValue,
  maxHeight = 36,
}: {
  label?: string;
  tooltip?: string;
  draggable?: boolean;
  addButtonLabel?: string;
  idField?: keyof T;
  nameField?: keyof T;
  allItems: T[];
  values: T[];
  setValues: (newOrder: T[]) => void;
  canDeleteItem?: (item: T) => boolean;
  onRowClick?: (item: T) => void;
  selectOnAdd?: boolean;
  getItemLabel?: (item: T) => string;
  createNewValue?: (opt: Option) => T;
  maxHeight?: number;
}) => {
  const getItemId = (item: T) =>
    item instanceof Object && idField && idField in item
      ? (item[idField] as string)
      : (item as string);

  const unselectedValues = allItems.every((item) => typeof item === "string")
    ? allItems.filter((item) => values.every((v) => v !== item))
    : allItems.filter((item) =>
        values.every((v) => getItemId(v) !== getItemId(item))
      );

  const handleDeleteItem = (item: T) => {
    setValues(values.filter((v) => v !== item).slice());
  };

  const getItemDisplayName =
    getItemLabel ??
    ((item: T) => {
      if (item instanceof Object && idField && idField in item) {
        return (
          nameField && nameField in item ? item[nameField] : item[idField]
        ) as string;
      }
      return item as string;
    });

  const createOptionFromValue = (item: T) => {
    const value =
      item instanceof Object && idField && idField in item
        ? (item[idField] as string)
        : (item as string);
    return { label: getItemDisplayName(item), value };
  };

  const getValueFromOption = (opt: Option) =>
    allItems.every((item) => typeof item === "string")
      ? (opt.value as T)
      : allItems.find((item) => (item[idField!] as string) === opt.value)!;

  const handleAddNewValue = (opt: Option) => {
    const newValue = createNewValue
      ? createNewValue(opt)
      : getValueFromOption(opt);
    setValues([newValue, ...values.slice()]);
    if (selectOnAdd && onRowClick) {
      onRowClick(newValue);
    }
  };

  const listContainerProps = {
    border: "1px",
    borderColor: "gray.200",
    borderRadius: "md",
    w: "full",
    overflowY: "hidden",
  } as ChakraProps;

  const innerList = draggable ? (
    <Box as={motion.div} layoutScroll {...listContainerProps}>
      <Reorder.Group
        values={values}
        onReorder={(newValues) => setValues(newValues.slice())}
      >
        {values.map((item) => (
          <ScrollableListItem
            key={getItemId(item)}
            item={item}
            label={getItemDisplayName(item)}
            onDeleteItem={
              !canDeleteItem || (canDeleteItem && canDeleteItem(item))
                ? handleDeleteItem
                : undefined
            }
            onRowClick={onRowClick}
            draggable
            maxH={maxHeight}
          />
        ))}
      </Reorder.Group>
    </Box>
  ) : (
    <Box {...listContainerProps}>
      <List>
        {values.map((item) => (
          <ScrollableListItem
            key={getItemId(item)}
            item={item}
            label={getItemDisplayName(item)}
            onRowClick={onRowClick}
            onDeleteItem={handleDeleteItem}
            maxH={maxHeight}
          />
        ))}
      </List>
    </Box>
  );

  return values.length ? (
    <Flex align="start" direction="column" w="full" gap={4}>
      {label ? (
        <Label htmlFor="test" fontSize="xs" my={0} mr={1}>
          {label}
        </Label>
      ) : null}
      {tooltip ? <QuestionTooltip label={tooltip} /> : null}
      {innerList}
      {unselectedValues.length ? (
        <ScrollableListAdd
          label={addButtonLabel ?? "Add new"}
          options={unselectedValues.map((value) =>
            createOptionFromValue(value)
          )}
          onOptionSelected={handleAddNewValue}
        />
      ) : null}
    </Flex>
  ) : (
    <ScrollableListAdd
      label={addButtonLabel ?? "Add new"}
      options={unselectedValues.map((value) => createOptionFromValue(value))}
      onOptionSelected={handleAddNewValue}
    />
  );
};

export default ScrollableList;
