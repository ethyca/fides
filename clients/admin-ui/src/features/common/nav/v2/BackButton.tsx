import {
  ArrowBackIcon,
  Flex,
  FlexProps,
  IconButton,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";

/**
 * A back button meant to send the user to the upper level of the nav
 * For example, /consent/privacy-notices/new would go back to /consent/privacy-notices
 * */
const BackButton = ({
  backPath,
  ...props
}: { backPath: string } & FlexProps) => (
  // In general Layout provides a default top padding. But on pages with
  // Back buttons, we want the Back button to be higher and for the page to be less top-padded
  <Flex alignItems="center" mb={6} {...props}>
    <NextLink href={backPath} passHref>
      <IconButton
        aria-label="Back"
        icon={<ArrowBackIcon />}
        mr={2}
        size="xs"
        variant="outline"
      />
    </NextLink>
    <NextLink href={backPath} passHref>
      <Text as="a" fontSize="sm" fontWeight="500">
        Back
      </Text>
    </NextLink>
  </Flex>
);

export default BackButton;
