import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  BoxProps,
  Text,
} from "fidesui";
import { Fragment, ReactNode, useState } from "react";

import { TreeNode } from "./types";

interface Props {
  nodes: TreeNode[];
  focusedKey?: string;
  renderHover?: (node: TreeNode) => React.ReactNode;
  renderTag?: (node: TreeNode) => React.ReactNode;
}
const AccordionTree = ({
  nodes,
  focusedKey,
  renderHover,
  renderTag,
}: Props) => {
  const [hoverNode, setHoverNode] = useState<TreeNode | undefined>(undefined);
  /**
   * Recursive function to generate the accordion tree
   */
  const createTree = (node: TreeNode, level: number = 0) => {
    const isHovered = hoverNode?.value === node.value;
    const isFocused = focusedKey === node.value;
    // some nodes render as AccordionItems and some as just Boxes, but
    // we want to keep their styling similar, so pass them the same props
    const itemProps: BoxProps = {
      borderBottom: "1px solid",
      borderColor: "gray.200",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      pl: level * 3,
      _hover: { bg: "gray.50" },
      onMouseEnter: () => {
        setHoverNode(node);
      },
      onMouseLeave: () => {
        setHoverNode(undefined);
      },
    };
    const hoverContent = isHovered && renderHover ? renderHover(node) : null;

    if (node.children.length === 0) {
      return (
        <Box py={2} {...itemProps}>
          <Box display="flex" alignItems="center">
            <Text
              data-testid={`item-${node.label}`}
              pl={5} // AccordionButton's caret is 20px, so use 5 to line this up
              color={isFocused ? "complimentary.500" : undefined}
              mr={2}
            >
              {node.label}
            </Text>
            {renderTag ? renderTag(node) : null}
          </Box>
          {hoverContent}
        </Box>
      );
    }
    return (
      <AccordionItem p={0} border="none">
        <Box {...itemProps}>
          <AccordionButton
            _expanded={{ color: "complimentary.500" }}
            _hover={{ bg: "gray.50" }}
            pl={0}
            color={isFocused ? "complimentary.500" : undefined}
          >
            <AccordionIcon />
            <Text data-testid={`accordion-item-${node.label}`} mr={2}>
              {node.label}
            </Text>
            {renderTag ? renderTag(node) : null}
          </AccordionButton>
          {hoverContent}
        </Box>

        <AccordionPanel p={0}>
          {node.children.map((childNode) => (
            <Fragment key={childNode.value}>
              {createTree(childNode, level + 1) as ReactNode}
            </Fragment>
          ))}
        </AccordionPanel>
      </AccordionItem>
    );
  };
  return (
    <Box boxSizing="border-box">
      <Accordion allowMultiple>
        {nodes.map((child) => (
          <Box key={child.value}>{createTree(child)}</Box>
        ))}
      </Accordion>
    </Box>
  );
};

export default AccordionTree;
