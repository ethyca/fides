import { Handle, NodeProps, Position } from "@xyflow/react";
import { AntButton as Button, AntTypography as Typography } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import React, { useState } from "react";

export type SystemNodeData = {
  label: string;
  description?: string;
};

const DatamapSystemNode = ({ data, selected }: NodeProps) => {
  const nodeData = data as SystemNodeData;
  const [isHovered, setIsHovered] = useState(false);

  // Get button styling based on hover and selection state
  const getButtonStyle = () => {
    if (selected) {
      return {
        color: "white",
        backgroundColor: palette.FIDESUI_MINOS,
        boxShadow:
          "0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)",
        border: `1px solid ${palette.FIDESUI_PRIMARY_500}`,
      };
    }

    if (isHovered) {
      return {
        color: "white",
        backgroundColor: palette.FIDESUI_NEUTRAL_700,
        boxShadow:
          "0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)",
        border: `1px solid ${palette.FIDESUI_NEUTRAL_600}`,
      };
    }

    return {
      color: palette.FIDESUI_NEUTRAL_800,
      backgroundColor: palette.FIDESUI_NEUTRAL_50,
      boxShadow: "none",
      border: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
    };
  };

  const buttonStyle = getButtonStyle();

  return (
    <div
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        flexDirection: "column",
      }}
      data-testid="datamap-system-node"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <Button
        style={{
          height: "28px",
          maxWidth: "180px",
          transition:
            "background-color 300ms ease-in 0s, color 300ms ease 0s, border-color 300ms ease 0s, box-shadow 300ms ease 0s",
          color: buttonStyle.color,
          backgroundColor: buttonStyle.backgroundColor,
          boxShadow: buttonStyle.boxShadow,
          border: buttonStyle.border,
        }}
        type="text"
        role="button"
        aria-label={`System: ${nodeData.label}${nodeData.description ? `. ${nodeData.description}` : ""}`}
        tabIndex={0}
      >
        <Typography.Text ellipsis style={{ color: "inherit" }}>
          {nodeData.label}
        </Typography.Text>
      </Button>

      {/* Source handle (right) */}
      <Handle
        type="source"
        position={Position.Right}
        style={{
          width: 10,
          height: 10,
          background: palette.FIDESUI_NEUTRAL_200,
          border: `1px solid ${palette.FIDESUI_NEUTRAL_300}`,
          opacity: 0,
          pointerEvents: "none",
        }}
      />

      {/* Target handle (left) */}
      <Handle
        type="target"
        position={Position.Left}
        style={{
          width: 10,
          height: 10,
          background: palette.FIDESUI_NEUTRAL_200,
          border: `1px solid ${palette.FIDESUI_NEUTRAL_300}`,
          opacity: 0,
          pointerEvents: "none",
        }}
      />
    </div>
  );
};

export default DatamapSystemNode;
