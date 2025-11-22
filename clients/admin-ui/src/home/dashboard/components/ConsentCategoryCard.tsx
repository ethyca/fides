import { AntCard as Card, AntTypography as Typography, Box, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { Area, AreaChart, ResponsiveContainer, YAxis } from "recharts";
import * as React from "react";

interface ConsentCategoryCardProps {
  category: string;
  value: number;
  change: number; // positive for increase, negative for decrease
  trendData: number[]; // Array of values for the mini chart
}

/**
 * Consent category card component with trend indicator and mini chart
 */
export const ConsentCategoryCard = ({
  category,
  value,
  change,
  trendData,
}: ConsentCategoryCardProps) => {
  const isPositive = change > 0;
  const changeColor = isPositive
    ? palette.FIDESUI_SUCCESS
    : palette.FIDESUI_ERROR;
  const chartData = trendData.map((val, index) => ({ value: val, index }));
  // Determine chart color based on trend direction
  const chartColor = isPositive ? palette.FIDESUI_OLIVE : palette.FIDESUI_TERRACOTTA;
  // Generate a unique gradient ID for each card instance
  // Using a stable ID based on category and value to avoid re-renders
  const gradientId = React.useMemo(() => {
    // Create a stable hash from category and value
    const hash = `${category}-${value}`.replace(/[^a-zA-Z0-9]/g, '-');
    return `gradient-${hash}`;
  }, [category, value]);

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
      <Box p={4} flex={1} display="flex" flexDirection="column">
        {/* Category Name */}
        <Typography.Text style={{ fontSize: "14px", color: palette.FIDESUI_NEUTRAL_700, marginBottom: "16px", margin: 0 }}>
          {category}
        </Typography.Text>

        {/* Main Value */}
        <Text fontSize="24px" fontWeight="bold" color={palette.FIDESUI_MINOS} mb={2} lineHeight="32px">
          {value.toLocaleString()}
        </Text>

        {/* Change Indicator */}
        <Text fontSize="sm" fontWeight="medium" color={changeColor} mb={4}>
          {isPositive ? "↑" : "↓"} {Math.abs(change).toLocaleString()}
        </Text>
      </Box>

      {/* Mini Trend Chart - extends to border */}
      <Box height="50px" width="100%" margin={0} padding={0}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.8} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <YAxis hide domain={["dataMin", "dataMax"]} />
            <Area
              type="monotone"
              dataKey="value"
              stroke={chartColor}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Box>
    </Card>
  );
};
