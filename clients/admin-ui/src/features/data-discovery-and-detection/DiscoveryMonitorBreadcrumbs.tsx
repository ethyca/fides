import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "@fidesui/react";
import Link from "next/link";

import useDiscoveryRoutes from "./hooks/useDiscoveryRoutes";

interface DiscoveryMonitorBreadcrumbsProps {
  resourceUrn?: string;
  parentTitle: string;
  parentLink: string;
  onPathClick?: (urn: string) => void;
}

const DiscoveryMonitorBreadcrumbs: React.FC<
  DiscoveryMonitorBreadcrumbsProps
> = ({ resourceUrn, parentTitle, parentLink, onPathClick = () => {} }) => {
  const {} = useDiscoveryRoutes();

  const urnParts = resourceUrn ? resourceUrn.split(".") : [];

  return (
    <Breadcrumb
      separator="->"
      fontSize="2xl"
      fontWeight="medium"
      mb={5}
      data-testid="results-breadcrumb"
    >
      <BreadcrumbItem color={resourceUrn ? "gray.500" : "black"}>
        <BreadcrumbLink as={Link} href={parentLink}>
          {parentTitle}
        </BreadcrumbLink>
      </BreadcrumbItem>

      {!resourceUrn ? (
        <BreadcrumbItem color={resourceUrn ? "gray.500" : "black"}>
          <BreadcrumbLink>All activity</BreadcrumbLink>
        </BreadcrumbItem>
      ) : null}

      {urnParts.map((urnPart, index) => {
        // don't display  first part of the url since it's the monitor id again
        if (index === 0) {
          return null;
        }

        const isLastPart = index === urnParts.length - 1;

        return (
          <BreadcrumbItem
            key={urnPart}
            color={isLastPart ? "black" : "gray.500"}
          >
            <BreadcrumbLink
              onClick={() =>
                onPathClick(urnParts.slice(0, index + 1).join("."))
              }
            >
              {urnPart}
            </BreadcrumbLink>
          </BreadcrumbItem>
        );
      })}
    </Breadcrumb>
  );
};
export default DiscoveryMonitorBreadcrumbs;
