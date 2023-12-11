import {
  Badge,
  Box,
  Flex,
  Switch,
  Tag,
  Text,
  useDisclosure,
  useToast,
  WarningIcon,
} from "@fidesui/react";
import React, { ChangeEvent } from "react";
import { CellProps } from "react-table";

import ClipboardButton from "~/features/common/ClipboardButton";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { RTKResult } from "~/types/errors";

import { errorToastParams } from "../toast";

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

export const PaddedCell = <T extends object>({
  value,
}: CellProps<T, string>) => (
  <Text whiteSpace="normal" p={2}>
    {value}
  </Text>
);

export const ClipboardCell = <T extends object>({
  value,
}: CellProps<T, string>) => (
  <Flex alignItems="center">
    <Text mr={4}>{value}</Text>

    <ClipboardButton copyText={value} />
  </Flex>
);

export const DateCell = <T extends object>({ value }: CellProps<T, string>) =>
  new Date(value).toDateString();

type MapCellProps<T extends object> = CellProps<T, string> & {
  map: Map<string, string>;
  isPlainText?: boolean;
};

export const MapCell = <T extends object>({
  map,
  value,
  isPlainText,
}: MapCellProps<T>) => {
  const innerText = map.get(value) ?? value;
  if (isPlainText) {
    return (
      <Text whiteSpace="normal" p={2}>
        {innerText}
      </Text>
    );
  }
  return (
    <Badge
      size="sm"
      width="fit-content"
      data-testid="status-badge"
      textTransform="uppercase"
      fontWeight="400"
      color="gray.600"
      px={2}
    >
      {innerText}
    </Badge>
  );
};

export const MultiTagCell = <T extends object>({
  value,
  map,
}: CellProps<T, string[]> & { map?: Map<string, string> }) => {
  // If we are over a certain number, render an "..." instead of all of the tags
  const maxNum = 8;
  // eslint-disable-next-line no-nested-ternary
  const tags = value
    ? value.length > maxNum
      ? [...value.slice(0, maxNum), "..."]
      : value
    : [];
  if (tags.length === 0) {
    return <Text>None</Text>;
  }
  return (
    <Box whiteSpace="normal">
      {tags.map((v, idx) => (
        <Tag
          key={v}
          size="sm"
          backgroundColor="primary.400"
          color="white"
          mr={idx === value.length - 1 ? 0 : 3}
          mb={2}
        >
          {map && map.get(v) ? map.get(v) : v.replace(/_/g, "-")}
        </Tag>
      ))}
    </Box>
  );
};

type EnableCellProps<T extends object> = CellProps<T, boolean> & {
  onToggle: (data: boolean) => Promise<RTKResult>;
  title: string;
  message: string;
  /**
   * Disables the toggle. Can also pass a prop on `column`.
   * If either are true, then the toggle is disabled.
   */
  isDisabled?: boolean;
};

export const EnableCell = <T extends object>({
  value,
  column,
  onToggle,
  title,
  message,
  isDisabled,
}: EnableCellProps<T>) => {
  const modal = useDisclosure();
  const toast = useToast();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    const result = await onToggle(enable);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    }
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
        disabled={isDisabled || column.disabled}
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
