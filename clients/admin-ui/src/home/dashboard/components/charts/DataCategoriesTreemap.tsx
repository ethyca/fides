import { Box, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Tooltip, Treemap } from "recharts";
import * as React from "react";
import { useEffect, useRef, useState } from "react";

import { ChartContainer } from "../ChartContainer";
import { CustomTooltip } from "../CustomTooltip";
import { CHART_CONFIG, TREEMAP_COLORS } from "../../constants";
import type { DataCategoryData } from "../../types";

interface DataCategoriesTreemapProps {
  data: DataCategoryData[];
  title?: string;
  height?: number;
}

/**
 * Custom treemap content renderer
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
    // Return an empty group to satisfy Treemap content type expectations
    return <g />;
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
      TREEMAP_COLORS[index] ||
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
 * Treemap component for displaying data categories
 * Uses ResizeObserver for responsive sizing
 */
export const DataCategoriesTreemap = ({
  data,
  title = "Data Categories Treemap",
  height = CHART_CONFIG.treemap.defaultHeight,
}: DataCategoriesTreemapProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>(
    {
      width: CHART_CONFIG.treemap.minWidth,
      height: CHART_CONFIG.treemap.minHeight,
    }
  );

  useEffect(() => {
    if (!containerRef.current) return;

    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        const width = Math.max(rect.width, CHART_CONFIG.treemap.minWidth);
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
    <ChartContainer title={title} height={height}>
      <Box
        ref={containerRef}
        width="100%"
        height="100%"
        minWidth={0}
        minHeight={0}
        position="relative"
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
            <Text>Loading treemap...</Text>
          </Box>
        )}
      </Box>
    </ChartContainer>
  );
};
