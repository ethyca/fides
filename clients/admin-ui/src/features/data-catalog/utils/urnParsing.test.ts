import {
  parseResourceBreadcrumbsNoProject,
  parseResourceBreadcrumbsWithProject,
} from "~/features/data-catalog/utils/urnParsing";

const URL_PREFIX = "/url-prefix";

describe(parseResourceBreadcrumbsWithProject.name, () => {
  const URN = "monitor.project.dataset.table.field";
  const EXPECTED_TITLES = ["project", "dataset", "table", "field"];
  const EXPECTED_HREFS = [
    "/url-prefix/monitor.project",
    "/url-prefix/monitor.project/monitor.project.dataset",
    "/url-prefix/monitor.project/monitor.project.dataset.table",
    undefined,
  ];

  it("should return no breadcrumbs without a URN", () => {
    const result = parseResourceBreadcrumbsWithProject(undefined, URL_PREFIX);
    expect(result).toEqual([]);
  });

  it("should return no breadcrumbs with a short URN", () => {
    const result = parseResourceBreadcrumbsWithProject("monitor", URL_PREFIX);
    expect(result).toEqual([]);
  });

  it("should return the correct breadcrumbs when URN is provided", () => {
    const result = parseResourceBreadcrumbsWithProject(URN, URL_PREFIX);
    result.forEach((breadcrumb, idx) => {
      expect(breadcrumb.title).toEqual(EXPECTED_TITLES[idx]);
      expect(breadcrumb.href).toEqual(EXPECTED_HREFS[idx]);
    });
  });
});

describe(parseResourceBreadcrumbsNoProject.name, () => {
  const URN = "monitor.dataset.table.field";
  const EXPECTED_TITLES = ["dataset", "table", "field"];
  const EXPECTED_HREFS = [
    "/url-prefix/monitor.dataset",
    "/url-prefix/monitor.dataset.table",
    undefined,
  ];

  it("should return no breadcrumbs without a URN", () => {
    const result = parseResourceBreadcrumbsNoProject(undefined, URL_PREFIX);
    expect(result).toEqual([]);
  });

  it("should return no breadcrumbs with a short URN", () => {
    const result = parseResourceBreadcrumbsNoProject("monitor", URL_PREFIX);
    expect(result).toEqual([]);
  });

  it("should return the correct breadcrumbs when URN is provided", () => {
    const result = parseResourceBreadcrumbsNoProject(URN, URL_PREFIX);
    result.forEach((breadcrumb, idx) => {
      expect(breadcrumb.title).toEqual(EXPECTED_TITLES[idx]);
      expect(breadcrumb.href).toEqual(EXPECTED_HREFS[idx]);
    });
  });
});
