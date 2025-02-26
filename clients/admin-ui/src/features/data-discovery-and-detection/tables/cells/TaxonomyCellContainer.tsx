import React, { HTMLAttributes } from "react";

const TaxonomyCellContainer = ({
  children,
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => {
  return (
    <div
      className={`relative flex w-full flex-wrap items-center gap-2 overflow-x-auto py-2 ${
        className || ""
      }`}
      {...props}
    >
      {children}
    </div>
  );
};

export default TaxonomyCellContainer;
