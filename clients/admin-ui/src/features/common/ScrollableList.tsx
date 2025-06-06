import {
  AntButton as Button,
  AntSelect as Select,
  AntSpace as Space,
  Box,
  ChakraProps,
  DragHandleIcon,
  Flex,
  Icons,
  List,
  SmallAddIcon,
  Text,
} from "fidesui";
import { motion, Reorder, useDragControls } from "framer-motion";
import { useState } from "react";

import { Label, Option } from "~/features/common/form/inputs";
import { InfoTooltip } from "~/features/common/InfoTooltip";

const ScrollableListItem = <T extends unknown>({
  item,
  label,
  draggable,
  onDeleteItem,
  onEditItem,
  tooltip,
  onRowClick,
  maxH = 10,
  rowTestId,
}: {
  item: T;
  label: string;
  draggable?: boolean;
  onDeleteItem?: (item: T) => void;
  onEditItem?: (item: T) => void;
  tooltip?: string;
  onRowClick?: (item: T) => void;
  maxH?: number;
  rowTestId: string;
}) => {
  const dragControls = useDragControls();

  const content = (
    <Flex
      direction="row"
      gap={2}
      maxH={maxH}
      w="full"
      px={2}
      align="center"
      role="group"
      className="group"
      borderY="1px"
      my="-1px"
      borderColor="gray.200"
      _hover={onRowClick ? { bgColor: "gray.100" } : undefined}
      bgColor="white"
      position="relative"
    >
      {draggable && (
        <DragHandleIcon
          onPointerDown={(e) => dragControls.start(e)}
          cursor="grab"
        />
      )}
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
        overflow="clip"
        data-testid={rowTestId}
      >
        <Text
          fontSize="sm"
          userSelect="none"
          textOverflow="ellipsis"
          whiteSpace="nowrap"
          overflow="hidden"
        >
          {label}
        </Text>
        <InfoTooltip label={tooltip} />
      </Flex>
      <Space className="invisible absolute right-2 bg-white group-hover:visible">
        {onEditItem && (
          <Button
            aria-label="Edit"
            onClick={() => onEditItem(item)}
            icon={<Icons.Edit />}
            size="small"
            data-testid={`edit-${rowTestId}`}
          />
        )}
        {onDeleteItem && (
          <Button
            aria-label="Delete"
            onClick={() => onDeleteItem(item)}
            icon={<Icons.TrashCan />}
            size="small"
            data-testid={`delete-${rowTestId}`}
          />
        )}
      </Space>
    </Flex>
  );

  return draggable ? (
    <Reorder.Item value={item} dragListener={false} dragControls={dragControls}>
      {content}
    </Reorder.Item>
  ) : (
    content
  );
};

const ScrollableListAdd = ({
  label,
  options,
  onOptionSelected,
  baseTestId,
}: {
  label: string;
  options: Option[];
  onOptionSelected: (opt: Option) => void;
  baseTestId: string;
}) => {
  const [isAdding, setIsAdding] = useState<boolean>(false);
  const [selectValue, setSelectValue] = useState<Option | undefined>(undefined);

  const handleElementSelected = (value: Option) => {
    onOptionSelected(value);
    setIsAdding(false);
    setSelectValue(undefined);
  };

  return isAdding ? (
    <Box w="full">
      <Select
        labelInValue
        placeholder="Select..."
        filterOption={(input, option) =>
          (option?.label ?? "").toLowerCase().includes(input.toLowerCase())
        }
        value={selectValue}
        options={options}
        onChange={handleElementSelected}
        className="w-full"
        data-testid={`select-${baseTestId}`}
      />
    </Box>
  ) : (
    <Button
      onClick={() => setIsAdding(true)}
      data-testid={`add-${baseTestId}`}
      block
      icon={<SmallAddIcon boxSize={4} />}
      iconPosition="end"
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
  getTooltip,
  onRowClick,
  onEditItem,
  selectOnAdd,
  getItemLabel,
  createNewValue,
  maxHeight = 36,
  baseTestId,
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
  getTooltip?: (item: T) => string | undefined;
  onRowClick?: (item: T) => void;
  onEditItem?: (item: T) => void;
  selectOnAdd?: boolean;
  getItemLabel?: (item: T) => string;
  createNewValue?: (opt: Option) => T;
  maxHeight?: number;
  baseTestId: string;
}) => {
  const getItemId = (item: T) =>
    item instanceof Object && idField && idField in item
      ? (item[idField] as string)
      : (item as string);

  const unselectedValues = allItems.every((item) => typeof item === "string")
    ? allItems.filter((item) => values.every((v) => v !== item))
    : allItems.filter((item) =>
        values.every((v) => getItemId(v) !== getItemId(item)),
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
    if (selectOnAdd && onEditItem) {
      onEditItem(newValue);
    }
  };

  const listContainerProps = {
    border: "1px",
    borderColor: "gray.200",
    borderRadius: "md",
    w: "full",
    maxH: "8.5rem",
    overflowY: "auto",
  } as ChakraProps;

  const innerList = draggable ? (
    <Box as={motion.div} layoutScroll {...listContainerProps}>
      <Reorder.Group
        values={values}
        onReorder={(newValues) => setValues(newValues.slice())}
      >
        {values.map((item) => {
          const itemId = getItemId(item);
          return (
            <ScrollableListItem
              key={itemId}
              item={item}
              label={getItemDisplayName(item)}
              onDeleteItem={
                !canDeleteItem || (canDeleteItem && canDeleteItem(item))
                  ? handleDeleteItem
                  : undefined
              }
              onEditItem={onEditItem}
              onRowClick={onRowClick}
              draggable
              maxH={maxHeight}
              rowTestId={`${baseTestId}-row-${itemId}`}
              tooltip={
                getTooltip && getTooltip(item) ? getTooltip(item) : undefined
              }
            />
          );
        })}
      </Reorder.Group>
    </Box>
  ) : (
    <Box {...listContainerProps}>
      <List>
        {values.map((item) => {
          const itemId = getItemId(item);
          return (
            <ScrollableListItem
              key={itemId}
              item={item}
              label={getItemDisplayName(item)}
              onRowClick={onRowClick}
              onDeleteItem={handleDeleteItem}
              tooltip={
                getTooltip && getTooltip(item) ? getTooltip(item) : undefined
              }
              maxH={maxHeight}
              rowTestId={`${baseTestId}-row-${itemId}`}
            />
          );
        })}
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
      <InfoTooltip label={tooltip} />
      {innerList}
      {unselectedValues.length ? (
        <ScrollableListAdd
          label={addButtonLabel ?? "Add new"}
          options={unselectedValues.map((value) =>
            createOptionFromValue(value),
          )}
          onOptionSelected={handleAddNewValue}
          baseTestId={baseTestId}
        />
      ) : null}
    </Flex>
  ) : (
    <ScrollableListAdd
      label={addButtonLabel ?? "Add new"}
      options={unselectedValues.map((value) => createOptionFromValue(value))}
      onOptionSelected={handleAddNewValue}
      baseTestId={baseTestId}
    />
  );
};

export default ScrollableList;
