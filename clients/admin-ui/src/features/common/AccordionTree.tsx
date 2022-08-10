import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  BoxProps,
  Button,
  ButtonGroup,
  Text,
} from "@fidesui/react";
import { Fragment, useState } from "react";

import { TaxonomyEntityNode } from "../taxonomy/types";
import { TreeNode } from "./types";

interface ActionButtonProps {
  node: TaxonomyEntityNode;
  onEdit: (node: TaxonomyEntityNode) => void;
}
const ActionButtons = ({ node, onEdit }: ActionButtonProps) => (
  <ButtonGroup size="xs" isAttached variant="outline" data-testid="action-btns">
    <Button data-testid="edit-btn" onClick={() => onEdit(node)}>
      Edit
    </Button>
    <Button data-testid="delete-btn">Delete</Button>
  </ButtonGroup>
);

interface Props {
  nodes: TreeNode[];
  onEdit: (node: TaxonomyEntityNode) => void;
}
const AccordionTree = ({ nodes, onEdit }: Props) => {
  const [hoverNode, setHoverNode] = useState<TreeNode | undefined>(undefined);
  /**
   * Recursive function to generate the accordion tree
   */
  const createTree = (node: TreeNode, level: number = 0) => {
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

    if (node.children.length === 0) {
      return (
        <Box py={2} {...itemProps} data-testid={`item-${node.label}`}>
          <Text
            pl={5} // AccordionButton's caret is 20px, so use 5 to line this up
          >
            {node.label}
          </Text>
          {hoverNode?.value === node.value ? (
            <ActionButtons node={hoverNode} onEdit={onEdit} />
          ) : null}
        </Box>
      );
    }
    return (
      <AccordionItem
        p={0}
        border="none"
        data-testid={`accordion-item-${node.label}`}
      >
        <Box {...itemProps}>
          <AccordionButton
            _expanded={{ color: "complimentary.500" }}
            _hover={{ bg: "gray.50" }}
            pl={0}
          >
            <AccordionIcon />
            {node.label}
          </AccordionButton>
          {hoverNode?.value === node.value ? (
            <ActionButtons node={hoverNode} onEdit={onEdit} />
          ) : null}
        </Box>

        <AccordionPanel p={0}>
          {node.children.map((childNode) => (
            <Fragment key={childNode.value}>
              {createTree(childNode, level + 1)}
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
