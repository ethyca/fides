import {
  Box,
  Switch,
  Tag,
  Text,
  useDisclosure,
  WarningIcon,
} from "@fidesui/react";
import ConfirmationModal from "common/ConfirmationModal";
import React, { ChangeEvent } from "react";
import { CellProps } from "react-table";

export const TitleCell = <T extends object>({
  value,
}: CellProps<T, string>) => (
  <Text fontWeight="semibold" color="gray.600">
    {value}
  </Text>
);

export const WrappedCell = <T extends object>({
  value,
}: CellProps<T, string>) => <Text whiteSpace="normal">{value}</Text>;

export const DateCell = <T extends object>({ value }: CellProps<T, string>) =>
  new Date(value).toDateString();

type MapCellProps<T extends object> = CellProps<T, string> & {
  map: Map<string, string>;
};

export const MapCell = <T extends object>({ map, value }: MapCellProps<T>) => (
  <Tag size="sm" backgroundColor="primary.400" color="white">
    {map.get(value) ?? value}
  </Tag>
);

export const MultiTagCell = <T extends object>({
  value,
}: CellProps<T, string[]>) => {
  // If we are over a certain number, render an "..." instead of all of the tags
  const maxNum = 8;
  // eslint-disable-next-line no-nested-ternary
  const tags = value
    ? value.length > maxNum
      ? [...value.slice(0, maxNum), "..."]
      : value
    : [];
  return (
    <Box whiteSpace="normal">
      {tags.map((v, idx) => (
        <Tag
          key={v}
          size="sm"
          backgroundColor="primary.400"
          color="white"
          mr={idx === value.length - 1 ? 0 : 3}
          textTransform="uppercase"
          mb={2}
        >
          {v.replace(/_/g, "-")}
        </Tag>
      ))}
    </Box>
  );
};

type EnableCellProps<T extends object> = CellProps<T, boolean> & {
  onToggle: (data: boolean) => Promise<any>;
  title: string;
  message: string;
};

export const EnableCell = <T extends object>({
  value,
  column,
  onToggle,
  title,
  message,
}: EnableCellProps<T>) => {
  const modal = useDisclosure();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    await onToggle(enable);
  };

  const handleToggle = async (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
    if (checked) {
      await handlePatch({ enable: true });
    } else {
      modal.onOpen();
    }
  };

  return (
    <>
      <Switch
        colorScheme="complimentary"
        isChecked={!value}
        data-testid={`toggle-${column.Header}`}
        /**
         * It's difficult to use a custom column in react-table 7 since we'd have to modify
         * the declaration file. However, that modifies the type globally, so our datamap table
         * would also have issues. Ignoring the type for now, but should potentially revisit
         * if we update to react-table 8
         * https://github.com/DefinitelyTyped/DefinitelyTyped/discussions/59837
         */
        // @ts-ignore
        disabled={column.disabled}
        onChange={handleToggle}
      />
      <ConfirmationModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        onConfirm={() => {
          handlePatch({ enable: false });
          modal.onClose();
        }}
        title={title}
        message={<Text color="gray.500">{message}</Text>}
        continueButtonText="Confirm"
        isCentered
        icon={<WarningIcon color="orange.100" />}
      />
    </>
  );
};
