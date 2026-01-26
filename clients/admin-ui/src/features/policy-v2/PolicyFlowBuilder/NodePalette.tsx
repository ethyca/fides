import React from "react";
import { Button, ChakraBox as Box, ChakraText as Text, Icons } from "fidesui";

import { FlowNodeType } from "./types";
import styles from "./NodePalette.module.scss";

interface NodePaletteProps {
  onAddRule: () => void;
}

interface NodeTypeInfo {
  type: FlowNodeType;
  label: string;
  color: string;
  description: string;
}

const NODE_TYPES: NodeTypeInfo[] = [
  {
    type: "match",
    label: "Match Condition",
    color: "#3182ce",
    description: "Filter data by category, use, or subject",
  },
  {
    type: "constraint",
    label: "Constraint",
    color: "#805ad5",
    description: "Apply privacy or context constraints",
  },
  {
    type: "action",
    label: "Action",
    color: "#38a169",
    description: "Allow or deny access",
  },
];

export const NodePalette = ({ onAddRule }: NodePaletteProps) => {
  const handleDragStart = (
    event: React.DragEvent<HTMLDivElement>,
    nodeType: FlowNodeType,
  ) => {
    const { dataTransfer } = event;
    dataTransfer.effectAllowed = "copy";
    dataTransfer.setData("application/reactflow", nodeType);
    dataTransfer.setData("nodeType", nodeType);
  };

  return (
    <Box className={styles.palette}>
      <Box className={styles.header}>
        <Text className={styles.title}>Node Types</Text>
      </Box>

      <Box className={styles.content}>
        <Box className={styles.nodeList}>
          {NODE_TYPES.map((nodeInfo) => (
            <Box
              key={nodeInfo.type}
              className={styles.nodeItem}
              draggable
              onDragStart={(e) => handleDragStart(e, nodeInfo.type)}
              data-testid={`palette-node-${nodeInfo.type}`}
            >
              <Box
                className={styles.nodeIcon}
                style={{ backgroundColor: nodeInfo.color }}
              >
                <Box className={styles.nodeSymbol}>
                  {nodeInfo.type === "match" && "M"}
                  {nodeInfo.type === "constraint" && "C"}
                  {nodeInfo.type === "action" && "A"}
                </Box>
              </Box>
              <Box className={styles.nodeInfo}>
                <Text className={styles.nodeLabel}>{nodeInfo.label}</Text>
                <Text className={styles.nodeDescription}>
                  {nodeInfo.description}
                </Text>
              </Box>
            </Box>
          ))}
        </Box>

        <Box className={styles.divider} />

        <Box className={styles.actions}>
          <Button
            type="primary"
            block
            icon={<Icons.Add />}
            onClick={onAddRule}
            data-testid="add-rule-button"
          >
            Add Rule
          </Button>
        </Box>
      </Box>
    </Box>
  );
};
