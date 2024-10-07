/**
 * This CheckboxTree does a few opinionated things to facilitate DataCategory selection
 *   * Indeterminate parents when not all children are selected
 *   * Separate "selected" and "checked" states, since only the most specific child is "selected".
 *     * However, the parents are not "selected"—they will either be "indeterminate", or "checked" depending
 *       on if the siblings are also "selected"
 *   * "Selected" children render expanded up until the child
 */

import { AntButton, Box, BoxProps, Checkbox, ChevronDownIcon } from "fidesui";
import { Fragment, ReactNode, useEffect, useState } from "react";

import { TreeNode } from "./types";

export const getAncestorsAndCurrent = (nodeName: string) => {
  const splitNames = nodeName.split(".");
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
};

export const ancestorIsSelected = (selected: string[], nodeName: string) => {
  const ancestors = getAncestorsAndCurrent(nodeName).filter(
    (a) => a !== nodeName,
  );
  const intersection = selected.filter((s) => ancestors.includes(s));
  return intersection.length > 0;
};

const matchNodeOrDescendant = (value: string, match: string) => {
  if (value === match) {
    return true;
  }
  if (value.startsWith(`${match}.`)) {
    return true;
  }
  return false;
};

export const getDescendantsAndCurrent = (
  nodes: TreeNode[],
  nodeName: string,
  result?: TreeNode[],
) => {
  const descendants: TreeNode[] = result ?? [];
  nodes.forEach((node) => {
    if (node.children) {
      getDescendantsAndCurrent(node.children, nodeName, descendants);
    }
    if (matchNodeOrDescendant(node.value, nodeName)) {
      descendants.push(node);
    }
  });
  return descendants;
};

interface CheckboxItemProps {
  node: TreeNode;
  isChecked: boolean;
  onChecked: (node: TreeNode) => void;
  isExpanded: boolean;
  onExpanded: (node: TreeNode) => void;
  isIndeterminate: boolean;
  isDisabled: boolean;
  children?: ReactNode[];
}
const CheckboxItem = ({
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
        minHeight={8}
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
          <AntButton
            data-testid={`expand-${label}`}
            aria-label={isExpanded ? "collapse" : "expand"}
            icon={<ChevronDownIcon boxSize={5} />}
            type="text"
            onClick={() => onExpanded(node)}
            className={isExpanded ? "rotate-180" : undefined}
          />
        ) : null}
      </Box>
      {children && <Box ml={5}>{children}</Box>}
    </Box>
  );
};

interface CheckboxTreeProps extends BoxProps {
  nodes: TreeNode[];
  selected: string[];
  onSelected: (newSelected: string[]) => void;
}

const CheckboxTree = ({
  nodes,
  selected,
  onSelected,
  ...props
}: CheckboxTreeProps) => {
  const [checked, setChecked] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<string[]>([]);

  useEffect(() => {
    // if something is selected, we should expand the checkbox to show it
    // from i.e. ["account.contact.city"] get ["account", "account.contact", "account.contact.city"]
    const nestedAncestorNames = selected.map((s) => getAncestorsAndCurrent(s));
    const ancestorNames = nestedAncestorNames.reduce(
      (acc, value) => acc.concat(value),
      [],
    );

    // also, if a parent is selected, check all of its descendants
    const nestedDescendantNames = selected.map((s) =>
      getDescendantsAndCurrent(nodes, s),
    );
    const descendantNames = nestedDescendantNames
      .reduce((acc, value) => acc.concat(value), [])
      .map((d) => d.value);

    const nodeNames = Array.from(
      new Set([...ancestorNames, ...descendantNames]),
    );
    setExpanded(nodeNames);
    setChecked(nodeNames);
  }, [selected, nodes]);

  const handleChecked = (node: TreeNode) => {
    let newChecked: string[] = [];
    let newSelected: string[] = [];
    if (checked.indexOf(node.value) >= 0) {
      // take advantage of dot notation here for unchecking children
      newChecked = checked.filter((s) => !matchNodeOrDescendant(s, node.value));
      newSelected = selected.filter(
        (s) => !matchNodeOrDescendant(s, node.value),
      );
    } else {
      // we need to mark all descendants as checked, though these are not
      // technically 'selected'
      const descendants = getDescendantsAndCurrent(nodes, node.value).map(
        (d) => d.value,
      );
      newChecked = [...checked, ...descendants];
      newSelected = [...selected, node.value];
    }
    setChecked(newChecked);
    onSelected(newSelected);
  };

  const handleExpanded = (node: TreeNode) => {
    if (expanded.indexOf(node.value) >= 0) {
      // take advantage of dot notation here for unexpanding children
      setExpanded(
        expanded.filter((c) => !matchNodeOrDescendant(c, node.value)),
      );
    } else {
      setExpanded([...expanded, node.value]);
    }
  };

  /**
   * Recursive function to generate the checkbox tree
   */
  const createTree = (node: TreeNode) => {
    if (node.children) {
      const isChecked = checked.indexOf(node.value) >= 0;
      const isExpanded = expanded.indexOf(node.value) >= 0;
      const thisDescendants = getDescendantsAndCurrent(nodes, node.value);
      const isIndeterminate =
        isChecked &&
        node.children.length > 0 &&
        checked.filter((s) => s.startsWith(`${node.value}.`)).length + 1 !==
          thisDescendants.length;
      const isDisabled = ancestorIsSelected(selected, node.value);

      return (
        <CheckboxItem
          node={node}
          isChecked={isChecked}
          onChecked={handleChecked}
          isExpanded={isExpanded}
          onExpanded={handleExpanded}
          isDisabled={isDisabled}
          isIndeterminate={isIndeterminate}
        >
          {isExpanded
            ? node.children.map((childNode) => (
                <Fragment key={childNode.value}>
                  {createTree(childNode) as ReactNode}
                </Fragment>
              ))
            : undefined}
        </CheckboxItem>
      );
    }
    return null;
  };

  return (
    <Box {...props}>
      {nodes.map((child) => (
        <Box key={child.value}>{createTree(child)}</Box>
      ))}
    </Box>
  );
};

export default CheckboxTree;
