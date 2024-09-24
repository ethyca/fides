import { Td, Tfoot, Tr } from "fidesui";
import React, { ReactNode } from "react";

type Props = {
  totalColumns: number;
  children: ReactNode;
};

export const FidesTableFooter = ({ totalColumns, children }: Props) => (
  <Tfoot backgroundColor="neutral.50">
    <Tr>
      <Td
        colSpan={totalColumns}
        px={4}
        py={2}
        borderTop="1px solid"
        borderColor="neutral.200"
      >
        {children}
      </Td>
    </Tr>
  </Tfoot>
);
