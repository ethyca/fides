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
    fontSize="md"
    fontWeight="normal"
    mb={5}
    separator="/"
  />
);
export default DatasetBreadcrumbs;
