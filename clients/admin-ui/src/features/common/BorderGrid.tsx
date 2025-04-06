import { Box, SimpleGrid } from "fidesui";
import { chunk } from "lodash";
import { ReactNode } from "react";

import classes from "./BorderGrid.module.css";

interface Props<T> {
  columns: number;
  items: T[];
  renderItem: (item: T) => ReactNode;
}
const BorderGrid = <T extends unknown>({
  columns,
  items,
  renderItem,
}: Props<T>) => {
  const chunks = chunk(items, columns);

  return (
    <Box>
      {chunks.map((parent, index, { length }) => (
        <Box
          key={JSON.stringify(parent)}
          className={classes["grid-row"]}
          // Add bottom border only if last row is complete and there is more than 1 row rendered
          borderBottomWidth={
            length > 1 && index === length - 1 && parent.length === columns
              ? "0.5px"
              : undefined
          }
        >
          <SimpleGrid columns={columns}>
            {parent.map((child) => (
              <Box key={JSON.stringify(child)} className={classes["grid-item"]}>
                {renderItem(child)}
              </Box>
            ))}
          </SimpleGrid>
        </Box>
      ))}
    </Box>
  );
};

export default BorderGrid;
