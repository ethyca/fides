import { NextBreadcrumbProps } from "~/features/common/nav/v2/NextBreadcrumb";

const URN_SEPARATOR = ".";

export const getProjectName = (urn: string) => {
  const urnParts = urn.split(URN_SEPARATOR);
  return urnParts[1];
};

export const parseResourceBreadcrumbsWithProject = (
  urn: string | undefined,
  urlPrefix: string,
) => {
  if (!urn) {
    return [];
  }
  const urnParts = urn.split(URN_SEPARATOR);
  const projectUrn = urnParts.splice(0, 2).join(URN_SEPARATOR);
  const subResourceUrns: NextBreadcrumbProps["items"] = [];
  urnParts.reduce((prev, current, idx) => {
    const isLast = idx === urnParts.length - 1;
    const next = `${prev}${URN_SEPARATOR}${current}`;
    subResourceUrns.push({
      title: current,
      href: !isLast ? `${urlPrefix}/${projectUrn}/${next}` : undefined,
    });
    return next;
  }, `${projectUrn}`);

  return [
    {
      title: getProjectName(projectUrn),
      href: `${urlPrefix}/${projectUrn}`,
    },
    ...subResourceUrns,
  ];
};
