import { Box, Heading, Spacer, Stack } from "fidesui";

const SystemFormInputGroup = ({
  heading,
  HeadingButton,
  children,
}: {
  heading: string;
  HeadingButton?: React.ReactNode;
  children?: React.ReactNode;
}) => (
  <Stack spacing={4}>
    <Box
      maxWidth="720px"
      border="1px"
      borderColor="gray.200"
      borderRadius={6}
      overflow="visible"
      mt={6}
    >
      <Box
        backgroundColor="gray.50"
        px={6}
        py={4}
        display="flex"
        flexDirection="row"
        alignItems="center"
        borderBottom="1px"
        borderColor="gray.200"
        borderTopRadius={6}
      >
        <Heading as="h3" size="xs">
          {heading}
        </Heading>
        {HeadingButton ? (
          <>
            <Spacer />
            {/* @ts-ignore */}
            <HeadingButton />
          </>
        ) : null}
      </Box>

      <Stack spacing={4} px={6} py={6}>
        {children}
      </Stack>
    </Box>
  </Stack>
);

export default SystemFormInputGroup;
