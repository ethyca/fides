import { Flex, Typography } from "fidesui";
import React from "react";

const DatasetOption = ({
  label,
  value,
}: {
  label?: React.ReactNode;
  value?: string | number;
}): React.ReactNode => {
  if (String(value) === String(label)) {
    return label;
  }
  return (
    <Flex align="center" gap={8} className="w-full">
      <span className="flex-1 truncate">{label}</span>
      <Typography.Text
        type="secondary"
        className="max-w-72 shrink-0 truncate text-right"
      >
        {String(value)}
      </Typography.Text>
    </Flex>
  );
};

export default DatasetOption;
