import { AntFlex as Flex, AntTypography as Typography } from "fidesui";
import React from "react";

const { Text } = Typography;

interface ResultsSelectedCountProps {
  selectedIds: React.Key[];
  totalResults?: number;
}

export const ResultsSelectedCount = ({
  selectedIds,
  totalResults,
}: ResultsSelectedCountProps) => {
  const hasSelections = selectedIds.length > 0;

  return (
    <Flex gap={8} align="center">
      {hasSelections && (
        <>
          <Text strong data-testid="selected-count">
            {selectedIds.length} selected
          </Text>
          {totalResults !== undefined && <Text type="secondary"> / </Text>}
        </>
      )}
      {totalResults !== undefined && (
        <Text type="secondary" data-testid="total-results">
          {totalResults} results
        </Text>
      )}
    </Flex>
  );
};
