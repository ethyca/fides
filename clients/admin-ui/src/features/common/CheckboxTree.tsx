/**
 * This CheckboxTree does a few opinionated things to facilitate DataCategory selection
 *   * Indeterminate parents when not all children are selected
 *   * Separate "selected" and "checked" states, since only the most specific child is "selected".
 *     * However, the parents are not "selected"—they will either be "indeterminate", or "checked" depending
 *       on if the siblings are also "selected"
 *   * "Selected" children render expanded up until the child
 */

import { Box, Checkbox, IconButton } from "@fidesui/react";
import { Fragment, ReactNode, useEffect, useState } from "react";

import { ArrowDownLineIcon, ArrowUpLineIcon } from "./Icon";

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

export const getMostSpecificDescendants = (nodeNames: string[]) => {
  // take advantage of dot notation. this is n^2 time, but the input array
  // likely won't be very long
  const leaves: string[] = [];
  nodeNames.forEach((nodeName) => {
    const ancestors = nodeNames.filter((n) => n.startsWith(nodeName));
    if (ancestors.length === 1) {
      leaves.push(nodeName);
    }
  });
  return leaves;
};

export const getDescendantsAndCurrent = (
  nodes: CheckboxNode[],
  nodeName: string,
  result?: CheckboxNode[]
) => {
  const descendants: CheckboxNode[] = result ?? [];
  nodes.forEach((node) => {
    if (node.children) {
      getDescendantsAndCurrent(node.children, nodeName, descendants);
    }
    if (node.value.startsWith(nodeName)) {
      descendants.push(node);
    }
  });
  return descendants;
};

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
  isIndeterminate: boolean;
  children?: ReactNode;
}
const CheckboxItem = ({
  node,
  isChecked,
  onChecked,
  isExpanded,
  onExpanded,
  isIndeterminate,
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
          isChecked={isIndeterminate ? false : isChecked}
          isIndeterminate={isIndeterminate}
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
  selected: string[];
  onSelected: (newSelected: string[]) => void;
}

const CheckboxTree = ({ nodes, selected, onSelected }: CheckboxTreeProps) => {
  const [checked, setChecked] = useState<string[]>([]);
  const [expanded, setExpanded] = useState<string[]>([]);

  useEffect(() => {
    // if something is selected, we should expand the checkbox to show it
    // from i.e. ["account.contact.city"] get ["account", "account.contact", "account.contact.city"]
    const nestedAncestorNames = selected.map((s) => getAncestorsAndCurrent(s));
    const ancestorNames = nestedAncestorNames.reduce(
      (acc, value) => acc.concat(value),
      []
    );

    // also, if a parent is selected, check all of its descendants
    const nestedDescendantNames = selected.map((s) =>
      getDescendantsAndCurrent(nodes, s)
    );
    const descendantNames = nestedDescendantNames
      .reduce((acc, value) => acc.concat(value), [])
      .map((d) => d.value);

    const nodeNames = Array.from(
      new Set([...ancestorNames, ...descendantNames])
    );
    setExpanded(nodeNames);
    setChecked(nodeNames);
  }, [selected, nodes]);

  const handleChecked = (node: CheckboxNode) => {
    let newChecked: string[] = [];
    let newSelected: string[] = [];
    if (checked.indexOf(node.value) >= 0) {
      // take advantage of dot notation here for unchecking children
      newChecked = checked.filter((s) => !s.startsWith(node.value));
      // have to also filter selected so that unselecting children
      // will not make parents selected
      newSelected = selected.filter((s) => !s.startsWith(node.value));
    } else {
      const descendants = getDescendantsAndCurrent(nodes, node.value).map(
        (d) => d.value
      );
      newChecked = [...checked, ...descendants];
      newSelected = newChecked;
    }
    setChecked(newChecked);
    // we want to make sure to only save the most specific descendant
    const descendants = getMostSpecificDescendants(newSelected);
    onSelected(descendants);
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
      const thisDescendants = getDescendantsAndCurrent(nodes, node.value);
      const isIndeterminate =
        isChecked &&
        node.children.length > 0 &&
        checked.filter((s) => s.startsWith(node.value)).length !==
          thisDescendants.length;

      return (
        <CheckboxItem
          node={node}
          isChecked={isChecked}
          onChecked={handleChecked}
          isExpanded={isExpanded}
          onExpanded={handleExpanded}
          isIndeterminate={isIndeterminate}
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
