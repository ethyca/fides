// Verify that getPageMetadata includes the noindex robots directive to prevent search engine indexing.

import getPageMetadata from "~/app/server-utils/getPageMetadata";

jest.mock("~/app/server-utils/getPrivacyCenterEnvironment", () => ({
  __esModule: true,
  default: jest.fn().mockResolvedValue({ config: null }),
}));

describe(getPageMetadata, () => {
  it("includes the noindex robots directive", async () => {
    const metadata = await getPageMetadata();
    expect(metadata.robots).toEqual({ index: false });
  });
});
