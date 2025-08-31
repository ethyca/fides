import { AntButton as Button, Code } from "fidesui";
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
    <Button variant="text" onClick={resetErrorBoundary}>
      Try again
    </Button>
  </ErrorLayout>
);

export default Error;
