import { Box } from "@fidesui/react";
import { isArray } from "lodash";
import { isValidElement, ReactElement } from "react";

import Breadcrumbs, { BreadcrumbsProps } from "~/features/common/Breadcrumbs";

interface PageHeaderProps {
  breadcrumbs: BreadcrumbsProps["breadcrumbs"] | ReactElement | false;
  isSticky?: boolean;
  extra?: ReactElement;
}

const PageHeader: React.FC<PageHeaderProps> = ({
  breadcrumbs,
  isSticky = true,
  extra,
}) => (
  <Box
    bgColor="white"
    paddingY={5}
    {...(isSticky ? { position: "sticky", top: 0, left: 0, zIndex: 10 } : {})}
  >
    {isArray(breadcrumbs) && (
      <Box marginBottom={isValidElement(extra) ? 4 : 0}>
        <Breadcrumbs breadcrumbs={breadcrumbs} />
      </Box>
    )}
    {isValidElement(breadcrumbs) && breadcrumbs}
    {isValidElement(extra) && extra}
  </Box>
);

export default PageHeader;
