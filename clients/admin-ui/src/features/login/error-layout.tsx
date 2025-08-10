import Image from "common/Image";
import { AntButton as Button, Box, Center } from "fidesui";
import NextLink from "next/link";

const ErrorLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <Center
      h="100%"
      w="100%"
      display="flex"
      justifyContent="center"
      flexDirection="column"
      rowGap={10}
    >
      <Box display={["none", "none", "block"]}>
        <Image src="/logo.svg" alt="Fides logo" width={205} height={46} />
      </Box>
      {children}
      <NextLink href="/login" passHref legacyBehavior>
        <Button type="primary">Back to Login</Button>
      </NextLink>
    </Center>
  );
};

export default ErrorLayout;
