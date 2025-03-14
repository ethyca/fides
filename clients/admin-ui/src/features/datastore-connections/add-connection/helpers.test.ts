import { describe, expect, it } from "@jest/globals";

import { formatKey } from "~/features/datastore-connections/add-connection/helpers";

const TEST_CASES = [
  ["Test Key with Spaces", "test_key_with_spaces"],
  ["test.key.with.dots", "test_key_with_dots"],
  ["Test Key with Spaces and Dots.", "test_key_with_spaces_and_dots_"],
  ["TestKeyWithNoSpacesOrDots", "testkeywithnospacesordots"],
  ["test_key_with_no_changes", "test_key_with_no_changes"],
];

describe(formatKey.name, () => {
  it("should format the key to lower case and replace spaces and dots with underscores", () => {
    TEST_CASES.forEach(([key, expected]) => {
      const result = formatKey(key);
      expect(result).toEqual(expected);
    });
  });
});
