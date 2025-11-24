import {
  privacyCenterPagesCspHeader,
  staticPageCspHeader,
} from "~/app/server-utils/recommendedSecurityHeaders";

describe("recommended security headers", () => {
  it("templates and flattens the static csp header", () => {
    expect(
      staticPageCspHeader({
        fidesApiHost: "fides.example.com",
        geolocationApiHost: "geolocation.example.com",
      }),
    ).toMatchSnapshot();
  });

  it.each([true, false])(
    "templates and flattens privacy center csp header when isDev is %s,"
    (isDev) => {
      expect(
        privacyCenterPagesCspHeader({
          fidesApiHost: "fides.example.com",
          geolocationApiHost: "geolocation.example.com",
          isDev,
          nonce: "random-nonce-string",
        }),
      ).toMatchSnapshot();
    },
  );
});
