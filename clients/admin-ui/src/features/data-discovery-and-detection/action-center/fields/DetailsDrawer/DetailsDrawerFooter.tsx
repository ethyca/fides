import { AntButton as Button, AntFlex as Flex } from "fidesui";

import { isNotEmpty } from "~/utils/array";

import type { DetailsDrawerProps } from "./types";

export const DetailsDrawerFooter = ({
  itemKey,
  actions,
}: {
  itemKey: string;
  actions: NonNullable<DetailsDrawerProps["actions"]>;
}) =>
  isNotEmpty(actions) ? (
    <Flex gap="small" justify="flex-end">
      {actions.map(({ callback, label }, index) => (
        <Button
          onClick={() => callback(itemKey)}
          key={label}
          type={index === actions.length - 1 ? "primary" : "default"}
        >
          {label}
        </Button>
      ))}
    </Flex>
  ) : null;
