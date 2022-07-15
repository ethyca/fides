import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  Box,
  Button,
  ButtonGroup,
  Text,
} from "@fidesui/react";
import { Fragment, useState } from "react";

import { TreeNode } from "./types";

const ActionButtons = () => (
  <ButtonGroup size="xs" isAttached variant="outline">
    <Button>Edit</Button>
    <Button>Delete</Button>
  </ButtonGroup>
);

interface Props {
  nodes: TreeNode[];
}
const AccordionTree = ({ nodes }: Props) => {
  const [hoverNode, setHoverNode] = useState<TreeNode | undefined>(undefined);
  /**
   * Recursive function to generate the accordion tree
   */
  const createTree = (node: TreeNode) => {
    // some nodes render as AccordionItems and some as just Boxes, but
    // we want to keep their styling similar, so pass them the same props
    const itemProps = {
      // TODO: these borders are cut a little short, need to figure out CSS
      borderBottom: "1px solid",
      borderColor: "gray.200",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      _hover: { bg: "gray.50" },
      onMouseEnter: () => {
        setHoverNode(node);
      },
    };

    if (node.children.length === 0) {
      return (
        <Box
          pl={9}
          py={2}
          {...itemProps}
          display="flex"
          justifyContent="space-between"
        >
          <Text>{node.label}</Text>
          {hoverNode?.value === node.value ? <ActionButtons /> : null}
        </Box>
      );
    }
    return (
      <AccordionItem py={0} border="none">
        <Box {...itemProps}>
          <AccordionButton _expanded={{ color: "complimentary.500" }}>
            <AccordionIcon />
            {node.label}
          </AccordionButton>
          {hoverNode?.value === node.value ? <ActionButtons /> : null}
        </Box>

        <AccordionPanel py={0} pr={0}>
          {node.children.map((childNode) => (
            <Fragment key={childNode.value}>{createTree(childNode)}</Fragment>
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
