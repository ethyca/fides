import { Badge, BadgeProps } from "fidesui";
import React from "react";

const ResultStatusBadge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (props, ref) => {
    return (
      <Badge
        fontSize="xs"
        fontWeight="normal"
        textTransform="none"
        ref={ref}
        {...props}
      >
        {props.children}
      </Badge>
    );
  },
);

ResultStatusBadge.displayName = "ResultStatusBadge";

export default ResultStatusBadge;
