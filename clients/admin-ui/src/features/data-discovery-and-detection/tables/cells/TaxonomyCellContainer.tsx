import { Wrap, WrapProps } from "fidesui";
import React from "react";

const TaxonomyCellContainer = React.forwardRef<HTMLDivElement, WrapProps>(
  ({ children, ...props }, ref) => {
    return (
      <Wrap
        py={2}
        alignItems="center"
        position="relative"
        width="100%"
        gap={2}
        overflowX="auto"
        ref={ref}
        {...props}
      >
        {children}
      </Wrap>
    );
  },
);

TaxonomyCellContainer.displayName = "TaxonomyCellContainer";

export default TaxonomyCellContainer;
