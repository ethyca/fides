import { Wrap, WrapProps } from "fidesui";
import React from "react";

const TaxonomyCellContainer = ({ children, ...props }: WrapProps) => {
  return (
    <Wrap
      py={2}
      alignItems="center"
      position="relative"
      width="100%"
      gap={2}
      overflowX="auto"
      {...props}
    >
      {children}
    </Wrap>
  );
};

export default TaxonomyCellContainer;
