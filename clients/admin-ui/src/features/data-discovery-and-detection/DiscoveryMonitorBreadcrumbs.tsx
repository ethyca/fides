import { Breadcrumb, BreadcrumbItem, BreadcrumbLink } from "fidesui";
import NextLink from "next/link";

interface DiscoveryMonitorBreadcrumbsProps {
  resourceUrn?: string;
  parentTitle: string;
  parentLink: string;
  onPathClick?: (urn: string) => void;
}

const DiscoveryMonitorBreadcrumbs = ({
  resourceUrn,
  parentTitle,
  parentLink,
  onPathClick = () => {},
}: DiscoveryMonitorBreadcrumbsProps) => {
  const urnParts = resourceUrn ? resourceUrn.split(".") : [];

  return (
    <Breadcrumb
      separator="->"
      fontSize="2xl"
      fontWeight="semibold"
      mb={5}
      data-testid="results-breadcrumb"
    >
      <BreadcrumbItem color={resourceUrn ? "gray.500" : "black"}>
        <BreadcrumbLink as={NextLink} href={parentLink}>
          {parentTitle}
        </BreadcrumbLink>
      </BreadcrumbItem>

      {!resourceUrn ? (
        <BreadcrumbItem color={resourceUrn ? "gray.500" : "black"}>
          <BreadcrumbLink>All activity</BreadcrumbLink>
        </BreadcrumbItem>
      ) : null}

      {urnParts.map((urnPart, index) => {
        // don't display the first or second parts of the URN (monitor ID or
        // database) because there's no table view for them
        if (index === 0 || index === 1) {
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
