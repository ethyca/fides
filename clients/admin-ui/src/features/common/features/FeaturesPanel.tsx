import {
  Box,
  Button,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerFooter,
  DrawerHeader,
  DrawerOverlay,
  FormControl,
  FormLabel,
  Grid,
  Switch,
  Text,
  UseDisclosureReturn,
} from "@fidesui/react";

import { CloseSolidIcon } from "~/features/common/Icon";

import { FLAG_NAMES, useFlags } from "./features.slice";
import { FlagValue } from "./types";

const FlagControl = ({
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
    </FormControl>
  );
};

const FeaturesPanel = ({
  isOpen,
  onClose,
}: Pick<UseDisclosureReturn, "isOpen" | "onClose">) => {
  const { flags, defaults, override, reset } = useFlags();

  return (
    <Drawer placement="right" isOpen={isOpen} onClose={onClose} size="md">
      <DrawerOverlay />
      <DrawerContent data-testid="edit-drawer-content" py={2} pr={2}>
        <Box display="flex" justifyContent="flex-end" mr={2}>
          <Button
            variant="ghost"
            onClick={onClose}
            data-testid="close-drawer-btn"
          >
            <CloseSolidIcon />
          </Button>
        </Box>

        <DrawerHeader py={2} display="flex" alignItems="center">
          <Text>Feature Flags</Text>
        </DrawerHeader>

        <DrawerBody>
          <Grid gridTemplateColumns="1fr 2fr">
            {FLAG_NAMES.map((flag) => (
              <FlagControl
                key={flag}
                flag={flag}
                value={flags[flag]}
                defaultValue={defaults[flag]}
                override={override}
              />
            ))}
          </Grid>
        </DrawerBody>

        <DrawerFooter justifyContent="flex-start">
          <Button size="sm" onClick={() => reset()}>
            Reset
          </Button>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
};

export default FeaturesPanel;
