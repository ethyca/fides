import { Box, FormControl, FormLabel, Switch, Text } from "@fidesui/react";

import { camelToSentenceCase } from "~/features/common/utils";

import { FLAG_CONFIG, FLAG_NAMES } from "./features.slice";
import { FlagValue } from "./types";

export const FlagControl = ({
  flag,
  value,
  defaultValue,
  override,
}: {
  flag: (typeof FLAG_NAMES)[number];
  value: FlagValue;
  defaultValue: FlagValue;
  override: (args: {
    flag: (typeof FLAG_NAMES)[number];
    value: boolean;
  }) => void;
}) => {
  if (typeof value !== "boolean") {
    // Only supporting modifying boolean flags for now.
    return (
      <>
        <Text fontSize="sm">{flag}</Text>
        <Text fontSize="sm">{value}</Text>
      </>
    );
  }

  return (
    <FormControl display="contents">
      <Box justifySelf="center">
        <Switch
          colorScheme={value !== defaultValue ? "yellow" : "blue"}
          id={`flag-${flag}`}
          isChecked={value}
          onChange={() =>
            override({
              flag,
              value: !value,
            })
          }
        />
      </Box>

      <Box>
        <FormLabel
          margin={0}
          fontSize="sm"
          htmlFor={`flag-${flag}`}
          title={flag}
        >
          {camelToSentenceCase(flag)}
        </FormLabel>
      </Box>

      <Box>
        <Text fontSize="sm">{FLAG_CONFIG[flag].description}</Text>
      </Box>
    </FormControl>
  );
};

export default FlagControl;
