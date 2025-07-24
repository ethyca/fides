import { Icons } from "fidesui";

import { NextBreadcrumbProps } from "~/features/common/nav/NextBreadcrumb";

const URN_SEPARATOR = ".";

export const getProjectName = (urn: string) => {
  const urnParts = urn.split(URN_SEPARATOR);
  return urnParts[1];
};

const RESOURCE_ICONS = [
  <Icons.Layers key="layers" />,
  <Icons.Table key="table" />,
  <Icons.ShowDataCards key="field" style={{ transform: "rotate(-90deg)" }} />,
];

export const parseResourceBreadcrumbsWithProject = (
  urn: string | undefined,
  urlPrefix: string,
) => {
  if (!urn) {
    return [];
  }
  const urnParts = urn.split(URN_SEPARATOR);
  if (urnParts.length < 2) {
    return [];
  }
  const projectUrn = urnParts.splice(0, 2).join(URN_SEPARATOR);
  const subResourceUrns: NextBreadcrumbProps["items"] = [];

  urnParts.reduce((prev, current, idx) => {
    const isLast = idx === urnParts.length - 1;
    const next = `${prev}${URN_SEPARATOR}${current}`;
    subResourceUrns.push({
      title: current,
      href: !isLast ? `${urlPrefix}/${projectUrn}/${next}` : undefined,
      icon: RESOURCE_ICONS[idx],
    });
    return next;
  }, projectUrn);

  return [
    {
      title: getProjectName(projectUrn),
      href: `${urlPrefix}/${projectUrn}`,
      icon: <Icons.Db2Database />,
    },
    ...subResourceUrns,
  ];
};

export const parseResourceBreadcrumbsNoProject = (
  urn: string | undefined,
  urlPrefix: string,
) => {
  if (!urn) {
    return [];
  }

  const urnParts = urn.split(URN_SEPARATOR);
  if (urnParts.length < 2) {
    return [];
  }
  const monitorId = urnParts.shift();
  const subResourceUrns: NextBreadcrumbProps["items"] = [];

  urnParts.reduce((prev, current, idx) => {
    const isLast = idx === urnParts.length - 1;
    const next = `${prev}${URN_SEPARATOR}${current}`;
    subResourceUrns.push({
      title: current,
      href: !isLast ? `${urlPrefix}/${next}` : undefined,
      icon: RESOURCE_ICONS[idx],
    });
    return next;
  }, monitorId);

  return subResourceUrns;
};
