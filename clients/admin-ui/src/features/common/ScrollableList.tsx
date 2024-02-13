import { AddIcon, DeleteIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  DragHandleIcon,
  Flex,
  IconButton,
  List,
  Spacer,
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
}: {
  item: T;
  label: string;
  onDeleteItem: (item: T) => void;
  draggable?: boolean;
}) => {
  const dragControls = useDragControls();

  return (
    <Reorder.Item value={item} dragListener={false} dragControls={dragControls}>
      <Flex
        direction="row"
        p={2}
        gap={2}
        maxH={10}
        align="center"
        role="group"
        borderBottom="1px"
        borderColor="gray.200"
        bgColor="white"
      >
        {draggable ? (
          <DragHandleIcon
            onPointerDown={(e) => dragControls.start(e)}
            cursor="grab"
          />
        ) : null}
        <Text fontSize="sm">{label}</Text>
        <Spacer />
        <IconButton
          aria-label="Delete"
          onClick={() => onDeleteItem(item)}
          icon={<DeleteIcon />}
          size="xs"
          variant="outline"
          visibility="hidden"
          _groupHover={{ visibility: "visible" }}
        />
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
  getItemLabel,
  createNewValue,
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
  getItemLabel?: (item: T) => string;
  createNewValue?: (opt: Option) => T;
}) => {
  const getItemId = (item: T) => {
    return item instanceof Object && idField && idField in item
      ? (item[idField] as string)
      : (item as string);
  };

  const unselectedValues = allItems.every((item) => typeof item === "string")
    ? allItems.filter((item) => values.every((v) => v !== item))
    : allItems.filter((item) =>
        values.every((v) => getItemId(v) !== getItemId(item))
      );

  // console.log("all: ", allItems);
  // console.log("unselected: ", unselectedValues);
  // console.log("selected: ", values);

  const handleDeleteItem = (item: T) => {
    setValues(values.filter((v) => v !== item));
  };

  const getItemDisplayName =
    getItemLabel ??
    ((item: T) => {
      if (item instanceof Object && idField && idField in item) {
        return (
          nameField && nameField in item ? item[nameField] : item[idField]
        ) as string;
      } else {
        return item as string;
      }
    });

  const createOptionFromValue = (item: T) =>
    item instanceof Object
      ? { label: getItemDisplayName(item), value: item[idField!] as string }
      : {
          label: item as string,
          value: item as string,
        };

  const getValueFromOption = (opt: Option) =>
    allItems.every((item) => typeof item === "string")
      ? (opt.value as T)
      : allItems.find((item) => (item[idField!] as string) === opt.value)!;

  const handleAddNewValue = (opt: Option) => {
    setValues([
      createNewValue ? createNewValue(opt) : getValueFromOption(opt),
      ...values,
    ]);
  };

  const innerList = draggable ? (
    <Box
      as={motion.div}
      w="full"
      layoutScroll
      borderRadius="md"
      border="1px"
      borderColor="gray.200"
      maxH={44}
      overflowY="scroll"
    >
      <Reorder.Group
        values={values}
        onReorder={(values) => {
          console.log(values);
          setValues(values);
        }}
      >
        {values.map((item) => (
          <ScrollableListItem
            key={getItemId(item)}
            item={item}
            label={getItemDisplayName(item)}
            onDeleteItem={handleDeleteItem}
            draggable
          />
        ))}
      </Reorder.Group>
    </Box>
  ) : (
    <Box
      borderRadius="md"
      border="1px"
      borderColor="gray.200"
      minH={12}
      maxH={44}
      overflowY="scroll"
    >
      <List>
        {values.map((item, idx) => (
          <ScrollableListItem
            key={idx}
            item={item}
            label={getItemDisplayName(item)}
            onDeleteItem={handleDeleteItem}
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
      <ScrollableListAdd
        label={addButtonLabel ?? "Add new"}
        options={unselectedValues.map((value) => createOptionFromValue(value))}
        onOptionSelected={(option) =>
          setValues([...values, getValueFromOption(option)] as T[])
        }
      />
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
