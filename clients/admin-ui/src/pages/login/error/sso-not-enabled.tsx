import { AntAlert as Alert, AntButton as Button, Center } from "fidesui";
import NextLink from "next/link";

const SsoNotEnabled = () => {
  return (
    <Center
      h="100%"
      w="100%"
      display="flex"
      justifyContent="center"
      flexDirection="column"
      rowGap={10}
    >
      <Alert
        showIcon
        type="error"
        message="SSO is not enabled"
        description={
          <>Please contact your administrator or login another way.</>
        }
      />
      <NextLink href="/login" passHref legacyBehavior>
        <Button type="primary">Back to Login</Button>
      </NextLink>
    </Center>
  );
};

export default SsoNotEnabled;
