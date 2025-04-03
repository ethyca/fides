import { transformSystemsToCookies } from "../../features/vendor-transform";

const mockCookie = (name: string) => ({
  name,
  path: "/",
  domain: "example.com",
  type: "cookie",
  cookie_refresh: false,
  max_age_seconds: 86400,
  uses_non_cookie_access: false,
  purposes: [1, 2, 3, 4, 7],
  special_purposes: [],
  features: [],
  special_features: [],
  vendor_id: "gvl.780",
  vendor_name: "Aniview LTD",
  gvl_version: null,
});

describe("transformSystemsToCookies", () => {
  it("should transform systems with no cookies", () => {
    const systems = [
      {
        fides_key: "test_system",
        name: "Test System",
        privacy_declarations: [
          {
            name: "Store system data.",
            data_categories: ["system.operations", "user.contact"],
            data_use: "functional.service.improve",
            data_subjects: ["anonymous_user"],
            dataset_references: ["public"],
            cookies: [],
          },
        ],
        cookies: [],
      },
    ];
    const result = transformSystemsToCookies(systems);
    expect(result).toEqual([]);
  });

  it("should transform systems with one cookie", () => {
    const systems = [
      {
        fides_key: "test_system",
        name: "Test System",
        privacy_declarations: [
          {
            name: "Store system data.",
            data_categories: ["system.operations", "user.contact"],
            data_use: "functional.service.improve",
            data_subjects: ["anonymous_user"],
            dataset_references: ["public"],
            cookies: [mockCookie("cookie1")],
          },
        ],
        cookies: [mockCookie("cookie1")],
      },
    ];
    const result = transformSystemsToCookies(systems);
    expect(result).toEqual([mockCookie("cookie1")]);
  });

  it("should transform systems with multiple cookies", () => {
    const systems = [
      {
        fides_key: "test_system",
        name: "Test System",
        privacy_declarations: [
          {
            name: "Store system data.",
            data_categories: ["system.operations", "user.contact"],
            data_use: "functional.service.improve",
            data_subjects: ["anonymous_user"],
            dataset_references: ["public"],
            cookies: [mockCookie("cookie1"), mockCookie("cookie2")],
          },
        ],
        cookies: [mockCookie("cookie1"), mockCookie("cookie2")],
      },
    ];
    const result = transformSystemsToCookies(systems);
    expect(result).toEqual([mockCookie("cookie1"), mockCookie("cookie2")]);
  });

  it("should transform systems with multiple data uses", () => {
    const systems = [
      {
        fides_key: "test_system",
        name: "Test System",
        privacy_declarations: [
          {
            name: "Store system data.",
            data_categories: ["system.operations", "user.contact"],
            data_use: "functional.service.improve",
            data_subjects: ["anonymous_user"],
            dataset_references: ["public"],
            cookies: [mockCookie("cookie1")],
          },
          {
            name: "Analyze customer behaviour.",
            data_categories: ["user.contact"],
            data_use: "functional.service.improve",
            data_subjects: ["anonymous_user"],
            dataset_references: ["public"],
            cookies: [mockCookie("cookie2")],
          },
        ],
        cookies: [mockCookie("cookie1"), mockCookie("cookie2")],
      },
    ];
    const result = transformSystemsToCookies(systems);
    expect(result).toEqual([mockCookie("cookie1"), mockCookie("cookie2")]);
  });
});
