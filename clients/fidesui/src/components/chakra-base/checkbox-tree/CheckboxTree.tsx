import { Box } from "fidesui";
import React, { Fragment, useEffect, useState } from "react";

import { CheckboxItem } from "./CheckboxItem";
import {
  ancestorIsSelected,
  getAncestorsAndCurrent,
  getDescendantsAndCurrent,
  matchNodeOrDescendant,
} from "./helpers";
import { TreeNode, TreeNodes } from "./types";

interface CheckboxTreeProps {
  nodes: TreeNodes;
  selected: string[];
  onSelected: (newSelected: string[]) => void;
}

/**
 * This CheckboxTree does a few opinionated things to facilitate DataCategory selection
 *   - Indeterminate parents when not all children are selected
 *   - Separate "selected" and "checked" states, since only the most specific child is "selected".
 *     - However, the parents are not "selected"—they will either be "indeterminate", or "checked"
 *       depending on if the siblings are also "selected"
 *   - "Selected" children render expanded up until the child
 */
export const CheckboxTree = ({
  nodes,
  selected,
  onSelected,
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
