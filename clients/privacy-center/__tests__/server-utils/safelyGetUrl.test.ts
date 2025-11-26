import { safelyGetHost } from "~/app/server-utils/safelyGetHost";

describe(safelyGetHost, () => {
  it("returns a string when a malformed URL is provided", () => {
    expect(safelyGetHost("this-is-not-a-valid-url")).toBe("");
  });

  it.each([
    {
      description: "host",
      url: "https://example.com/example-path",
      expected: "example.com",
    },
    {
      description: "host with subdomain",
      url: "https://geolocation.example.com/example-path",
      expected: "geolocation.example.com",
    },
  ])(
    "returns only the $description if given a full url",
    ({ url, expected }) => {
      expect(safelyGetHost(url)).toBe(expected);
    },
  );
});
