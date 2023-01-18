import { Box, FormControl, FormLabel, Switch, Text } from "@fidesui/react";

import { FLAG_CONFIG, FLAG_NAMES } from "./features.slice";
import { FlagValue } from "./types";

export const FlagControl = ({
  flag,
  value,
  defaultValue,
  override,
}: {
  flag: typeof FLAG_NAMES[number];
  value: FlagValue;
  defaultValue: FlagValue;
  override: (args: { flag: typeof FLAG_NAMES[number]; value: boolean }) => void;
}) => {
  if (typeof value !== "boolean") {
    // Only supporting modifying boolean flags for now.
    return (
      <>
        <Text>{flag}</Text>
        <Text>{value}</Text>
      </>
    );
  }

  return (
    <FormControl display="contents">
      <Box>
        <FormLabel htmlFor={`flag-${flag}`}>{flag}</FormLabel>
      </Box>

      <Box>
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
        <Text>{FLAG_CONFIG[flag].description}</Text>
      </Box>
    </FormControl>
  );
};

export default FlagControl;
