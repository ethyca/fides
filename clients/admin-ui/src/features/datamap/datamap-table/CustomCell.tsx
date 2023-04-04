import { ArrowDownLineIcon, ArrowUpLineIcon, Box, Text } from '@fidesui/react';
import React from 'react';
import { ColumnInstance, Row } from 'react-table';

import { useAppSelector } from '~/app/hooks';
import { selectDataSubjectsMap } from '~/features/data-subjects/data-subject.slice';
import { selectDataUsesMap } from '~/features/data-use/data-use.slice';

import {
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from '../constants';
import { DatamapRow, selectDataCategoriesMap } from '../datamap.slice';

interface CustomCellProps {
  // eslint-disable-next-line react/no-unused-prop-types
  row: Row<DatamapRow>;
  column: ColumnInstance<DatamapRow>;
  value: string;
}

const useCustomCell = () => {
  const [isCellExpanded, setIsCellExpanded] = React.useState(false);
  const [mouseOver, setMouseOver] = React.useState(false);
  const handleToggleExpanded = () => setIsCellExpanded(!isCellExpanded);
  const handleMouseEnter = () => {
    setMouseOver(true);
  };
  const handleMouseLeave = () => {
    setMouseOver(false);
  };
  return {
    mouseOver,
    isCellExpanded,
    handleToggleExpanded,
    handleMouseEnter,
    handleMouseLeave,
  };
};

type CellData = {
  label: string;
  expanded?: string;
};

/**
 * This hook translates a row's value into a user-friendly string, defaulting to the raw value
 * otherwise. The column's configuration can be used to identify how to translate the value.
 */
const useCustomCellLabel = ({
  column,
  value,
}: Pick<CustomCellProps, 'column' | 'value'>): CellData => {
  const categoriesMap = useAppSelector(selectDataCategoriesMap);
  const usesMap = useAppSelector(selectDataUsesMap);
  const subjectsMap = useAppSelector(selectDataSubjectsMap);

  if (column.id === DATA_CATEGORY_COLUMN_ID) {
    const mappedValue = value.split(', ').length
      ? value
          .split(', ')
          .map((v) => categoriesMap.get(v)?.name ?? v)
          .join(', ')
      : undefined;
    return {
      label: mappedValue || (categoriesMap.get(value)?.name ?? value),
      expanded: value,
    };
  }

  if (column.id === SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME) {
    return {
      label: value,
      expanded: usesMap.get(value)?.fides_key ?? value,
    };
  }

  if (column.id === SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME) {
    const mappedValue = value.split(', ').length
      ? value
          .split(', ')
          .map((v) => subjectsMap.get(v)?.fides_key ?? v)
          .join(', ')
      : undefined;
    return {
      label: value,
      expanded: mappedValue || (subjectsMap.get(value)?.fides_key ?? value),
    };
  }

  return {
    label: value,
  };
};

const CustomCell: React.FC<CustomCellProps> = ({ column, value }) => {
  const {
    isCellExpanded,
    handleMouseEnter,
    handleMouseLeave,
    handleToggleExpanded,
    mouseOver,
  } = useCustomCell();

  const cellData = useCustomCellLabel({ column, value });

  return (
    <Box
      position="relative"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      height="100%"
    >
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        height="100%"
      >
        <Box overflow="hidden" flex={1} p={2}>
          <Text
            fontSize="xs"
            lineHeight={4}
            fontWeight="medium"
            color="gray.600"
            isTruncated={!isCellExpanded}
          >
            {cellData.label}
          </Text>

          {/* Cells that have human-readable labels can be expanded to show the raw value. */}
          {isCellExpanded && cellData.expanded !== cellData.label ? (
            <Box fontStyle="italic" mt={2}>
              <Text
                fontSize="xs"
                lineHeight={4}
                fontWeight="medium"
                color="gray.600"
              >
                {cellData.expanded}
              </Text>
            </Box>
          ) : null}
        </Box>
        {(mouseOver || isCellExpanded) &&
        cellData.expanded &&
        cellData.expanded !== '' ? (
          <button
            type="button"
            style={{ position: 'relative', right: '10px' }}
            onClick={(e) => {
              e.stopPropagation();
              handleToggleExpanded();
            }}
          >
            {isCellExpanded ? (
              <ArrowUpLineIcon width="18px" height="18px" my="-4px" />
            ) : (
              <ArrowDownLineIcon width="18px" height="18px" my="-4px" />
            )}
          </button>
        ) : null}
      </Box>
    </Box>
  );
};

export default CustomCell;
