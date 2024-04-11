import useUrnPaths from "./hooks/useUrnPaths";

const DiscoveryMonitorBreadcrumbs = ({ urn: string }) => {
  const { navigateToUrn } = useUrnPaths();

  return <span>Breadcrumbs</span>;
};
export default DiscoveryMonitorBreadcrumbs;
