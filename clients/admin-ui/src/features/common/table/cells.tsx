import { Box, Tag, Text } from "@fidesui/react";
import { CellProps } from "react-table";

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
