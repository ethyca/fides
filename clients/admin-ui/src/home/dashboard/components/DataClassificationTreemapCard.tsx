import { AntCard as Card, AntTypography as Typography, Box } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Tooltip, Treemap } from "recharts";
import * as React from "react";
import { useEffect, useRef, useState } from "react";

import { CustomTooltip } from "./CustomTooltip";
import type { DataCategoryData } from "../types";

interface DataClassificationTreemapCardProps {
  systemName: string;
  data: DataCategoryData[];
  height?: number;
}

/**
 * Custom treemap content renderer for data classification cards
 */
const CustomTreemapContent = (
  props: any,
  dataArray: DataCategoryData[]
) => {
  const { x, y, width, height, payload, index } = props;

  // Validate props
  if (
    typeof x !== "number" ||
    typeof y !== "number" ||
    typeof width !== "number" ||
    typeof height !== "number" ||
    width <= 0 ||
    height <= 0
  ) {
    return null;
  }

  // Use index to look up the color from our data array
  let fillColor = palette.FIDESUI_INFO;

  if (
    typeof index === "number" &&
    index >= 0 &&
    index < dataArray.length
  ) {
    fillColor =
      dataArray[index]?.fill ||
      palette.FIDESUI_INFO;
  } else if (payload) {
    if (payload.fill) {
      fillColor = payload.fill;
    } else if (payload.name) {
      const found = dataArray.find((item) => item.name === payload.name);
      fillColor = found?.fill || palette.FIDESUI_INFO;
    }
  }

  const dataItem =
    typeof index === "number" && index >= 0 && index < dataArray.length
      ? dataArray[index]
      : payload;

  const name = dataItem?.name || payload?.name || "";
  const value = dataItem?.value || payload?.value || 0;

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        fill={fillColor}
        stroke={palette.FIDESUI_NEUTRAL_200}
        strokeWidth={2}
        rx={4}
      />
      {width > 60 && height > 40 && name && (
        <>
          <text
            x={x + width / 2}
            y={y + height / 2 - 6}
            textAnchor="middle"
            fill={palette.FIDESUI_MINOS}
            fontSize={11}
            fontWeight="500"
            dominantBaseline="central"
            stroke="none"
          >
            {name}
          </text>
          <text
            x={x + width / 2}
            y={y + height / 2 + 10}
            textAnchor="middle"
            fill={palette.FIDESUI_MINOS}
            fontSize={9}
            dominantBaseline="central"
            stroke="none"
          >
            {value}
          </text>
        </>
      )}
    </g>
  );
};

/**
 * Data Classification Treemap Card Component
 * Displays a treemap of data categories for a specific system
 */
export const DataClassificationTreemapCard = ({
  systemName,
  data,
  height = 300,
}: DataClassificationTreemapCardProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({
    width: 400,
    height,
  });

  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const width = Math.max(rect.width, 400);
        const containerHeight = Math.max(rect.height, height);
        setDimensions({ width, height: containerHeight });
      }
    };

    // Initial measurement
    updateDimensions();

    // Use ResizeObserver for better dimension tracking
    const resizeObserver = new ResizeObserver(() => {
      updateDimensions();
    });

    resizeObserver.observe(containerRef.current);

    // Fallback to window resize
    window.addEventListener("resize", updateDimensions);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateDimensions);
    };
  }, [height]);

  // Create a bound version of the content renderer with the data array
  const renderContent = React.useCallback(
    (props: any) => CustomTreemapContent(props, data),
    [data]
  );

  return (
    <Card
      style={{
        backgroundColor: palette.FIDESUI_NEUTRAL_50,
        borderRadius: "6px",
        border: `1px solid ${palette.FIDESUI_NEUTRAL_200}`,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: 0,
        overflow: "hidden",
      }}
      styles={{ body: { padding: 0 } }}
    >
      {/* System Name Header */}
      <Box p={4} pb={0}>
        <Typography.Text
          style={{
            fontSize: "14px",
            color: palette.FIDESUI_NEUTRAL_700,
            margin: 0,
            marginBottom: "16px",
          }}
        >
          {systemName}
        </Typography.Text>
      </Box>

      {/* Treemap Chart */}
      <Box
        ref={containerRef}
        width="100%"
        height={`${height}px`}
        minWidth={0}
        minHeight={0}
        position="relative"
        flex={1}
      >
        {dimensions.width > 0 && dimensions.height > 0 ? (
          <Treemap
            width={dimensions.width}
            height={dimensions.height}
            data={data}
            dataKey="value"
            nameKey="name"
            stroke={palette.FIDESUI_NEUTRAL_200}
            fill={palette.FIDESUI_INFO}
            content={renderContent}
          >
            <Tooltip content={<CustomTooltip />} />
          </Treemap>
        ) : (
          <Box
            width="100%"
            height="100%"
            display="flex"
            alignItems="center"
            justifyContent="center"
            color={palette.FIDESUI_NEUTRAL_500}
          >
            <Typography.Text>Loading treemap...</Typography.Text>
          </Box>
        )}
      </Box>
    </Card>
  );
};

