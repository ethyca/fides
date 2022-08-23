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
  onDelete: (node: TaxonomyEntityNode) => void;
}
const ActionButtons = ({ node, onEdit, onDelete }: ActionButtonProps) => {
  const showDelete = node.children.length === 0;
  return (
    <ButtonGroup
      size="xs"
      isAttached
      variant="outline"
      data-testid="action-btns"
      mr="2"
    >
      <Button data-testid="edit-btn" onClick={() => onEdit(node)}>
        Edit
      </Button>
      {showDelete ? (
        <Button data-testid="delete-btn" onClick={() => onDelete(node)}>
          Delete
        </Button>
      ) : null}
    </ButtonGroup>
  );
};

interface Props {
  nodes: TreeNode[];
  onEdit: (node: TaxonomyEntityNode) => void;
  onDelete: (node: TaxonomyEntityNode) => void;
  focusedKey?: string;
}
const AccordionTree = ({ nodes, onEdit, onDelete, focusedKey }: Props) => {
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

    if (node.children.length === 0) {
      return (
        <Box py={2} {...itemProps} data-testid={`item-${node.label}`}>
          <Text
            pl={5} // AccordionButton's caret is 20px, so use 5 to line this up
            color={isFocused ? "complimentary.500" : undefined}
          >
            {node.label}
          </Text>
          {isHovered ? (
            <ActionButtons
              node={hoverNode}
              onEdit={onEdit}
              onDelete={onDelete}
            />
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
            color={isFocused ? "complimentary.500" : undefined}
          >
            <AccordionIcon />
            {node.label}
          </AccordionButton>
          {isHovered ? (
            <ActionButtons
              node={hoverNode}
              onEdit={onEdit}
              onDelete={onDelete}
            />
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
