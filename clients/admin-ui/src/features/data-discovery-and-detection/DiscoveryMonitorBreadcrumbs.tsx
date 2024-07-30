import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "fidesui";
import { useRouter } from "next/router";

import { DatabaseIcon } from "~/features/common/Icon/detection-discovery-resource-types/DatabaseIcon";
import { DatasetIcon } from "~/features/common/Icon/detection-discovery-resource-types/DatasetIcon";
import { TableIcon } from "~/features/common/Icon/detection-discovery-resource-types/TableIcon";

interface DiscoveryMonitorBreadcrumbsProps {
  resourceUrn?: string;
  parentLink: string;
  onPathClick?: (urn: string) => void;
}

const MONITOR_BREADCRUMB_ICONS = [
  <DatabaseIcon key="database" />,
  <DatasetIcon key="dataset" boxSize={6} />,
  <TableIcon key="table" boxSize={6} />,
];

const DiscoveryMonitorBreadcrumbs = ({
  resourceUrn,
  parentLink,
  onPathClick = () => {},
}: DiscoveryMonitorBreadcrumbsProps) => {
  const router = useRouter();

  if (!resourceUrn) {
    return (
      <Breadcrumb
        separator="/"
        fontWeight={800}
        mb={5}
        data-testid="results-breadcrumb"
      >
        <BreadcrumbItem>
          <BreadcrumbLink>All activity</BreadcrumbLink>
        </BreadcrumbItem>
      </Breadcrumb>
    );
  }

  const urnParts = resourceUrn.split(".");

  return (
    <Breadcrumb separator="/" mb={5} data-testid="results-breadcrumb">
      {urnParts.map((urnPart, index) => {
        // don't render anything at the monitor level because there's no view for it
        if (index === 0) {
          return null;
        }

        // at the database level, link should go to "all activity" view
        const isDatabase = index === 1;
        const isLastPart = index === urnParts.length - 1;

        return (
          <BreadcrumbItem
            key={urnPart}
            fontWeight={isLastPart ? "semibold" : "normal"}
            color={isLastPart ? "gray.800" : "gray.500"}
          >
            {MONITOR_BREADCRUMB_ICONS[index - 1]}
            <BreadcrumbLink
              ml={1}
              onClick={() =>
                isDatabase
                  ? router.push(parentLink)
                  : onPathClick(urnParts.slice(0, index + 1).join("."))
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
