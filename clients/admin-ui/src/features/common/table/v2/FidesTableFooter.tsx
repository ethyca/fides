import { Td, Tfoot, Tr } from "@fidesui/react";
import React, { ReactNode } from "react";

type Props = {
  totalColumns: number;
  children: ReactNode;
};

export const FidesTableFooter = ({ totalColumns, children }: Props) => (
  <Tfoot backgroundColor="gray.50">
    <Tr>
      <Td colSpan={totalColumns} px={4} py={3.5}>
        {children}
      </Td>
    </Tr>
  </Tfoot>
);
