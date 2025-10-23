import { AntButton as Button, AntFlex as Flex } from "fidesui";

import type { DetailsDrawerProps } from "./types";

export const DetailsDrawerFooter = ({
  itemKey,
  actions,
}: {
  itemKey: React.Key;
  actions: NonNullable<DetailsDrawerProps["actions"]>;
}) => {
  const actionValues = Object.values(actions);
  return (
    <Flex gap="small" justify="flex-end">
      {actionValues.map(({ callback, label }, index) => (
        <Button
          onClick={() => callback(itemKey)}
          key={label}
          type={index === actionValues.length - 1 ? "primary" : "default"}
        >
          {label}
        </Button>
      ))}
    </Flex>
  );
};
