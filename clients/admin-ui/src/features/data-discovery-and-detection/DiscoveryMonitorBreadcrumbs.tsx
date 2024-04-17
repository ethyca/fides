import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "@fidesui/react";
import Link from "next/link";

import { DATA_DISCOVERY_MONITORS } from "../common/nav/v2/routes";
import useDiscoveryRoutes from "./hooks/useDiscoveryRoutes";

interface DiscoveryMonitorBreadcrumbsProps {
  monitorId?: string;
  resourceUrn?: string;
}

const DiscoveryMonitorBreadcrumbs: React.FC<
  DiscoveryMonitorBreadcrumbsProps
> = ({ monitorId, resourceUrn }) => {
  const { navigateToMonitorDetails, navigateToResourceDetails } =
    useDiscoveryRoutes();

  const urnParts = resourceUrn ? resourceUrn.split(".") : [];

  return (
    <Breadcrumb separator="->" fontSize="2xl" fontWeight="medium" mb={5}>
      <BreadcrumbItem color={monitorId ? "gray.500" : "black"}>
        <BreadcrumbLink as={Link} href={DATA_DISCOVERY_MONITORS}>
          Data Discovery
        </BreadcrumbLink>
      </BreadcrumbItem>

      {monitorId ? (
        <BreadcrumbItem color={resourceUrn ? "gray.500" : "black"}>
          <BreadcrumbLink
            onClick={() => navigateToMonitorDetails({ monitorId })}
          >
            {"{"}
            {monitorId}
            {"}"}
          </BreadcrumbLink>
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
              onClick={() => {
                navigateToResourceDetails({
                  monitorId: monitorId!,
                  // Join back to make the full arn for that element
                  resourceUrn: urnParts.slice(0, index + 1).join("."),
                });
              }}
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
