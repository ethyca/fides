import { Icons } from "fidesui";

import {
  NextBreadcrumb,
  NextBreadcrumbProps,
} from "../common/nav/NextBreadcrumb";

interface DiscoveryMonitorBreadcrumbsProps {
  resourceUrn?: string;
  parentLink: string;
  onPathClick?: (urn: string) => void;
}

export const DATA_BREADCRUMB_ICONS = [
  <Icons.Layers key="layers" />,
  <Icons.Db2Database key="dataset" />,
  <Icons.Table key="table" />,
  <Icons.ShowDataCards key="field" style={{ transform: "rotate(-90deg)" }} />,
];

const DiscoveryMonitorBreadcrumbs = ({
  resourceUrn,
  parentLink,
  onPathClick = () => {},
}: DiscoveryMonitorBreadcrumbsProps) => {
  const breadcrumbItems: NextBreadcrumbProps["items"] = [];

  if (!resourceUrn) {
    breadcrumbItems.push({
      title: "All activity",
    });
  }

  if (resourceUrn) {
    breadcrumbItems.push({
      title: "All activity",
      href: parentLink,
    });
    const urnParts = resourceUrn.split(".");
    urnParts.forEach((urnPart, index) => {
      // don't render anything at the monitor level because there's no view for it
      if (index === 0) {
        return;
      }

      breadcrumbItems.push({
        title: urnPart,
        icon: DATA_BREADCRUMB_ICONS[index - 1],
        onClick: (e) => {
          e.preventDefault();
          onPathClick(urnParts.slice(0, index + 1).join("."));
        },
      });
    });
  }

  return (
    <NextBreadcrumb data-testid="results-breadcrumb" items={breadcrumbItems} />
  );
};

export default DiscoveryMonitorBreadcrumbs;
