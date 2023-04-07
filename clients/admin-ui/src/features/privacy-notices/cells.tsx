import { Box, Switch, Tag, Text } from "@fidesui/react";
import { CellProps } from "react-table";

import { PrivacyNoticeResponse } from "~/types/api";

import { MECHANISM_MAP } from "./constants";

export const TitleCell = ({
  value,
}: CellProps<PrivacyNoticeResponse, string>) => (
  <Text fontWeight="semibold" color="gray.600">
    {value}
  </Text>
);

export const WrappedCell = ({
  value,
}: CellProps<PrivacyNoticeResponse, string>) => (
  <Text whiteSpace="normal">{value}</Text>
);

export const DateCell = ({ value }: CellProps<PrivacyNoticeResponse, string>) =>
  new Date(value).toDateString();

export const MechanismCell = ({
  value,
}: CellProps<PrivacyNoticeResponse, string>) => (
  <Tag size="sm" backgroundColor="primary.400" color="white">
    {MECHANISM_MAP.get(value) ?? value}
  </Tag>
);

export const MultiTagCell = ({
  value,
}: CellProps<PrivacyNoticeResponse, string[]>) => {
  // If we are over a certain number, render an "..." instead of all of the tags
  const maxNum = 8;
  const tags =
    value.length > maxNum ? [...value.slice(0, maxNum), "..."] : value;
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

export const ToggleCell = ({
  value,
  column,
  row,
}: CellProps<PrivacyNoticeResponse, boolean>) => (
  <Switch
    colorScheme="complimentary"
    isChecked={value}
    data-testid={`toggle-${column.Header}`}
    // @ts-ignore see comment below
    disabled={column.disabled}
    onChange={() => {
      /**
       * It's difficult to use a custom column in react-table 7 since we'd have to modify
       * the declaration file. However, that modifies the type globally, so our datamap table
       * would also have issues. Ignoring the type for now, but should potentially revisit
       * if we update to react-table 8
       * https://github.com/DefinitelyTyped/DefinitelyTyped/discussions/59837
       */
      // @ts-ignore
      column.onToggle(row.original.id);
    }}
  />
);
