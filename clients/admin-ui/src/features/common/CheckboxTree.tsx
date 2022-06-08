import { Box, Checkbox } from "@fidesui/react";
import { Fragment, ReactNode } from "react";

interface CheckboxNode {
  label: string;
  value: string;
  children: CheckboxNode[] | null;
}

interface CheckboxItemProps {
  node: CheckboxNode;
  isChecked: boolean;
  onChecked: (node: CheckboxNode) => void;
  children?: ReactNode;
}
const CheckboxItem = ({
  node,
  isChecked,
  onChecked,
  children,
}: CheckboxItemProps) => {
  const { value, label } = node;

  return (
    <Box>
      <Checkbox
        colorScheme="complimentary"
        value={value}
        isChecked={isChecked}
        onChange={() => onChecked(node)}
        ml={2}
        data-testid={`checkbox-${label}`}
      >
        {label}
      </Checkbox>
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
  const handleChecked = (node: CheckboxNode) => {
    if (checked.indexOf(node.value) >= 0) {
      // take advantage of dot notation here for unchecking children
      onChecked(checked.filter((c) => !c.startsWith(node.value)));
    } else {
      onChecked([...checked, node.value]);
    }
  };

  /**
   * Recursive function to generate the checkbox tree
   */
  const createTree = (node: CheckboxNode) => {
    if (node.children) {
      const isChecked = checked.indexOf(node.value) >= 0;
      console.log({ isChecked });
      return (
        <CheckboxItem
          node={node}
          isChecked={isChecked}
          onChecked={handleChecked}
        >
          {isChecked &&
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
