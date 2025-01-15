import { NextBreadcrumbProps } from "~/features/common/nav/v2/NextBreadcrumb";

const parseUrnToBreadcrumbs = (
  urn: string,
  urlPrefix: string,
): NextBreadcrumbProps["items"] => {
  if (!urn) {
    return [];
  }
  const urnParts = urn.split(".");
  const breadcrumbItems: NextBreadcrumbProps["items"] = [];
  urnParts.reduce((prev, current) => {
    const next = `${prev}.${current}`;
    breadcrumbItems.push({
      title: current,
      href: `${urlPrefix}/${next}`,
    });
    return next;
  });
  return breadcrumbItems;
};

export default parseUrnToBreadcrumbs;
