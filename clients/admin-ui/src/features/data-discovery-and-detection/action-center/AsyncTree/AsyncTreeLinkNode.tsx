import { Button, ButtonProps } from "fidesui";

import {
  AsyncTreeNodeComponentProps
} from "./types";

export const AsyncTreeDataLink = ({
  node,
  buttonProps,

}: Omit<AsyncTreeNodeComponentProps, 'actions'> & {buttonProps: ButtonProps }) => {
  const { title, disabled } = node
  if (!title) {
    return null;
  }

  return (
    <Button
      type="link"
      block
      disabled={disabled}
      {...buttonProps}
      className="p-0"
    >
      {typeof title === 'function' ? title(node) : title}
    </Button>
  );

};
