import { Box, Checkbox, IconButton } from "@fidesui/react";
import { Fragment, ReactNode, useEffect, useState } from "react";

import { ArrowDownLineIcon, ArrowUpLineIcon } from "./Icon";

interface CheckboxNode {
  label: string;
  value: string;
  children: CheckboxNode[] | null;
}

interface CheckboxItemProps {
  node: CheckboxNode;
  isChecked: boolean;
  onChecked: (node: CheckboxNode) => void;
  isExpanded: boolean;
  onExpanded: (node: CheckboxNode) => void;
  children?: ReactNode;
}
const CheckboxItem = ({
  node,
  isChecked,
  onChecked,
  isExpanded,
  onExpanded,
  children,
}: CheckboxItemProps) => {
  const { value, label } = node;
  const hasDescendants = node.children ? node.children.length > 0 : false;

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        _hover={{ backgroundColor: "gray.100" }}
      >
        <Checkbox
          colorScheme="complimentary"
          value={value}
          isChecked={isChecked}
          onChange={() => onChecked(node)}
          mx={2}
          data-testid={`checkbox-${label}`}
        >
          {label}
        </Checkbox>
        {hasDescendants ? (
          <IconButton
            data-testid={`expand-${label}`}
            aria-label={isExpanded ? "collapse" : "expand"}
            icon={isExpanded ? <ArrowUpLineIcon /> : <ArrowDownLineIcon />}
            variant="ghost"
            onClick={() => onExpanded(node)}
            size="sm"
          />
        ) : null}
      </Box>
      {children && <Box ml={5}>{children}</Box>}
    </Box>
  );
};

interface CheckboxTreeProps {
  nodes: CheckboxNode[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
}

const CheckboxTree = ({ nodes, checked, onChecked }: CheckboxTreeProps) => {
  const [expanded, setExpanded] = useState<string[]>([]);

  useEffect(() => {
    // if something is selected, we should expand the checkbox to show it
    // from i.e. ["account.contact.city"] get ["account", "account.contact", "account.contact.city"]
    const nestedNodeNames = checked.map((c) => {
      const splitNames = c.split(".");
      const ancestors: string[] = [];
      splitNames.forEach((name) => {
        const parent =
          ancestors.length > 0 ? ancestors[ancestors.length - 1] : null;
        if (!parent) {
          ancestors.push(name);
        } else {
          ancestors.push(`${parent}.${name}`);
        }
      });
      return ancestors;
    });
    const nodeNames = new Set(
      nestedNodeNames.reduce((acc, value) => acc.concat(value), [])
    );
    setExpanded(Array.from(nodeNames));
  }, [checked]);

  const handleChecked = (node: CheckboxNode) => {
    if (checked.indexOf(node.value) >= 0) {
      // take advantage of dot notation here for unchecking children
      onChecked(checked.filter((c) => !c.startsWith(node.value)));
    } else {
      onChecked([...checked, node.value]);
    }
  };

  const handleExpanded = (node: CheckboxNode) => {
    if (expanded.indexOf(node.value) >= 0) {
      // take advantage of dot notation here for unchecking children
      setExpanded(expanded.filter((c) => !c.startsWith(node.value)));
    } else {
      setExpanded([...expanded, node.value]);
    }
  };

  /**
   * Recursive function to generate the checkbox tree
   */
  const createTree = (node: CheckboxNode) => {
    if (node.children) {
      const isChecked = checked.indexOf(node.value) >= 0;
      const isExpanded = expanded.indexOf(node.value) >= 0;
      return (
        <CheckboxItem
          node={node}
          isChecked={isChecked}
          onChecked={handleChecked}
          isExpanded={isExpanded}
          onExpanded={handleExpanded}
        >
          {isExpanded &&
            node.children.map((childNode) => (
              <Fragment key={childNode.value}>{createTree(childNode)}</Fragment>
            ))}
        </CheckboxItem>
      );
    }
    return null;
  };

  return (
    <Box>
      {nodes.map((child) => (
        <Box key={child.value}>{createTree(child)}</Box>
      ))}
    </Box>
  );
};

export default CheckboxTree;
