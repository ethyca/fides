import {
  Box,
  Checkbox,
  ChevronDownIcon,
  ChevronUpIcon,
  IconButton,
} from "@fidesui/react";
import React, { ReactNode } from "react";

import { TreeNode } from "./types";

interface CheckboxItemProps {
  node: TreeNode;
  isChecked: boolean;
  onChecked: (node: TreeNode) => void;
  isExpanded: boolean;
  onExpanded: (node: TreeNode) => void;
  isIndeterminate: boolean;
  isDisabled: boolean;
  children?: ReactNode;
}

export const CheckboxItem = ({
  node,
  isChecked,
  onChecked,
  isExpanded,
  onExpanded,
  isIndeterminate,
  isDisabled,
  children,
}: CheckboxItemProps) => {
  const { value, label } = node;
  const hasDescendants = node.children ? node.children.length > 0 : false;

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        _hover={{ backgroundColor: "gray.100", cursor: "pointer" }}
        onClick={() => onExpanded(node)}
      >
        <Checkbox
          colorScheme="complimentary"
          value={value}
          isChecked={isIndeterminate ? false : isChecked}
          isIndeterminate={isIndeterminate}
          isDisabled={isDisabled}
          onChange={() => onChecked(node)}
          mx={2}
          data-testid={`checkbox-${label}`}
        >
          {label}
        </Checkbox>
        {hasDescendants ? (
          <IconButton
            variant="ghost"
            data-testid={`expand-${label}`}
            aria-label={isExpanded ? "collapse" : "expand"}
            size="sm"
            icon={
              isExpanded ? (
                <ChevronUpIcon boxSize="90%" />
              ) : (
                <ChevronDownIcon boxSize="90%" />
              )
            }
            onClick={() => onExpanded(node)}
          />
        ) : null}
      </Box>
      {children && <Box ml={5}>{children}</Box>}
    </Box>
  );
};

export default CheckboxItem;
