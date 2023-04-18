import {
  Box,
  Switch,
  Tag,
  Text,
  useDisclosure,
  WarningIcon,
} from "@fidesui/react";
import { ChangeEvent } from "react";
import { CellProps } from "react-table";

import ConfirmationModal from "~/features/common/ConfirmationModal";

import { FIELD_TYPE_MAP, MECHANISM_MAP } from "./constants";

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

export const MechanismCell = <T extends object>({
  value,
}: CellProps<T, string>) => (
  <Tag size="sm" backgroundColor="primary.400" color="white">
    {MECHANISM_MAP.get(value) ?? value}
  </Tag>
);

export const FieldTypeCell = <T extends object>({
  value,
}: CellProps<T, string>) => (
  <Tag size="sm" backgroundColor="primary.400" color="white">
    {FIELD_TYPE_MAP.get(value) ?? value}
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
  onToggle: (data: any) => Promise<any>;
};

export const EnableCell = <T extends object>({
  value,
  column,
  row,
  onToggle,
}: EnableCellProps<T>) => {
  const modal = useDisclosure();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    // @ts-ignore
    await onToggle([{ id: row.original.id, disabled: !enable }]);
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
        title="Disable privacy notice"
        message={
          <Text color="gray.500">
            Are you sure you want to disable this privacy notice? Disabling this
            notice means your users will no longer see this explanation about
            your data uses which is necessary to ensure compliance.
          </Text>
        }
        continueButtonText="Confirm"
        isCentered
        icon={<WarningIcon color="orange.100" />}
      />
    </>
  );
};
