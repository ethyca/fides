import { AntButton, ArrowBackIcon, Flex, FlexProps, Text } from "fidesui";
import NextLink from "next/link";

/**
 * A back button meant to send the user to the upper level of the nav
 * For example, /consent/privacy-notices/new would go back to /consent/privacy-notices
 * */
const BackButton = ({
  backPath,
  ...props
}: { backPath: string } & FlexProps) => (
  <Flex alignItems="center" mb={6} {...props}>
    <AntButton
      href={backPath}
      aria-label="Back"
      icon={<ArrowBackIcon />}
      className="mr-2"
      size="small"
    />
    <Text as={NextLink} href={backPath} fontSize="sm" fontWeight="500">
      Back
    </Text>
  </Flex>
);

export const BackButtonNonLink = ({
  onClick,
  ...props
}: { onClick: () => void } & FlexProps) => (
  <Flex
    alignItems="center"
    mt={-4}
    mb={3}
    onClick={onClick}
    cursor="pointer"
    {...props}
  >
    <AntButton
      aria-label="Back"
      icon={<ArrowBackIcon />}
      className="mr-2"
      size="small"
    />
    <Text as="a" fontSize="sm" fontWeight="500">
      Back
    </Text>
  </Flex>
);

export default BackButton;
