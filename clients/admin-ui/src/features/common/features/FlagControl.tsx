import {
  AntSwitch as Switch,
  Box,
  FormControl,
  FormLabel,
  Text,
} from "fidesui";

import { camelToSentenceCase } from "~/features/common/utils";

import { FLAG_CONFIG, FLAG_NAMES } from "./features.slice";
import { FlagValue } from "./types";

export const FlagControl = ({
  flag,
  value,
  override,
}: {
  flag: (typeof FLAG_NAMES)[number];
  value: FlagValue;
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

  // Do not render a toggle if the flag is marked as not able to be modified by the user
  if (FLAG_CONFIG[flag].userCannotModify) {
    return null;
  }

  return (
    <FormControl display="contents">
      <Box justifySelf="center">
        <Switch
          id={`flag-${flag}`}
          checked={value}
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
