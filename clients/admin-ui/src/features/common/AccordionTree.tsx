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
import { Fragment } from "react";

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
  /**
   * Recursive function to generate the accordion tree
   */
  const createTree = (node: TreeNode) => {
    // TODO: these borders are cut a little short, need to figure out CSS
    const borderProps = {
      borderBottom: "1px solid",
      borderColor: "gray.200",
    };
    if (node.children.length === 0) {
      return (
        <Box
          pl={9}
          py={2}
          _hover={{ bg: "gray.50" }}
          {...borderProps}
          display="flex"
          justifyContent="space-between"
        >
          <Text>{node.label}</Text>
          <ActionButtons />
        </Box>
      );
    }
    return (
      <AccordionItem py={0} border="none">
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          {...borderProps}
        >
          <AccordionButton _expanded={{ color: "complimentary.500" }}>
            <AccordionIcon />
            {node.label}
          </AccordionButton>
          {/* TODO: only show action buttons on hover */}
          <ActionButtons />
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
