import { Button, Code } from "fidesui";
import { FallbackProps } from "react-error-boundary";

import ErrorLayout from "~/components/ErrorLayout";

const Error = ({ error, resetErrorBoundary }: FallbackProps) => (
  <ErrorLayout
    title="Error"
    description="We're sorry, but an unexpected error occurred."
  >
    {error?.message ? (
      <Code
        height={200}
        width="80%"
        overflowY="auto"
        padding={4}
        fontWeight="semibold"
      >
        {error.message}
      </Code>
    ) : null}
    <Button
      width={320}
      as="a"
      bg="primary.800"
      _hover={{ bg: "primary.400" }}
      _active={{ bg: "primary.500" }}
      colorScheme="primary"
      onClick={resetErrorBoundary}
    >
      Try again
    </Button>
  </ErrorLayout>
);

export default Error;
