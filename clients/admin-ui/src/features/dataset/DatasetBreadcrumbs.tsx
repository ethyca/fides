/**
 * Renders the DatasetBreadcrumbs component with a few default styles
 * so every breadcrumb in the Dataset pages looks the same.
 *
 * @param breadcrumbProps - The props for the Breadcrumbs component.
 * @returns The rendered DatasetBreadcrumbs component.
 */

import React from "react";

import Breadcrumbs, { BreadcrumbsProps } from "~/features/common/Breadcrumbs";

const DatasetBreadcrumbs = (breadcrumbProps: BreadcrumbsProps) => (
  <Breadcrumbs
    {...breadcrumbProps}
    fontSize="sm"
    fontWeight="normal"
    mt={-1}
    mb={0}
    whiteSpace="nowrap"
    overflow="auto"
    separator="/"
    lastItemStyles={{ color: "black", fontWeight: "semibold" }}
  />
);
export default DatasetBreadcrumbs;
