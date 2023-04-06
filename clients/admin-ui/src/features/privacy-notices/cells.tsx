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
}: CellProps<PrivacyNoticeResponse, string[]>) => (
  <Box>
    {value.map((v, idx) => (
      <Tag
        key={v}
        size="sm"
        backgroundColor="primary.400"
        color="white"
        mr={idx === value.length - 1 ? 0 : 3}
        textTransform="uppercase"
      >
        {v}
      </Tag>
    ))}
  </Box>
);

export const ToggleCell = ({
  value,
  column,
  row,
}: CellProps<PrivacyNoticeResponse, boolean>) => (
  <Switch
    colorScheme="complimentary"
    isChecked={value}
    onChange={() => {
      column.onToggle(row.original.id);
    }}
  />
);
