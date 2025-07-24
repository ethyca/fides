import { describe, expect, it } from "@jest/globals";

import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";

const TEST_CASES = [
  ["Test Key with Spaces", "test_key_with_spaces"],
  ["test.key.with.dots", "test_key_with_dots"],
  ["Test Key with Spaces and Dots.", "test_key_with_spaces_and_dots_"],
  [
    "test key with url https://www.google.com/",
    "test_key_with_url_httpswww_google_com",
  ],
  ["TestKeyWithNoSpacesOrDots", "testkeywithnospacesordots"],
  ["test_key_with_no_changes", "test_key_with_no_changes"],
  ["test.key.with.dots", "test_key_with_dots"],
  ["test.key.with.dots and spaces", "test_key_with_dots_and_spaces"],
  [
    "test.key.with.dots.and spaces and.special.chars(áéíóúÑ)",
    "test_key_with_dots_and_spaces_and_special_chars",
  ],
];

describe(formatKey.name, () => {
  it("should format the key to lower case and replace spaces and dots with underscores", () => {
    TEST_CASES.forEach(([key, expected]) => {
      const result = formatKey(key);
      expect(result).toEqual(expected);
    });
  });
});
