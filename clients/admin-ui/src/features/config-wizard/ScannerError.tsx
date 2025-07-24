import {
  AntTag as Tag,
  Container,
  Divider,
  Heading,
  HStack,
  Stack,
  Text,
} from "fidesui";

import DocsLink from "~/features/common/DocsLink";
import { ParsedError } from "~/features/common/helpers";
import { ValidTargets } from "~/types/api";

import { DOCS_URL_AWS_PERMISSIONS, DOCS_URL_ISSUES } from "./constants";

const ErrorLog = ({ message }: { message: string }) => (
  <>
    <Divider />
    <Container maxH="50vh" overflow="auto">
      <Text as="pre" data-testid="error-log">
        {message}
      </Text>
    </Container>
    <Divider />
  </>
);

const ScannerError = ({
  error,
  scanType = "",
}: {
  error: ParsedError;
  scanType?: string;
}) => (
  <Stack data-testid="scanner-error" spacing="4">
    <HStack>
      <Tag color="error">Error</Tag>
      <Heading color="red.500" size="lg">
        Failed to Scan
      </Heading>
    </HStack>

    {error.status === 403 && scanType === ValidTargets.AWS ? (
      <>
        <Text data-testid="permission-msg">
          Fides was unable to scan AWS. It appears that the credentials were
          valid to login but they did not have adequate permission to complete
          the scan.
        </Text>

        {/* TODO(#892): A status of 403 should include a helpful log, which would appear here in an ErrorLog. */}

        <Text>
          To fix this issue, double check that you have granted{" "}
          <DocsLink href={DOCS_URL_AWS_PERMISSIONS}>
            the required permissions
          </DocsLink>{" "}
          to these credentials as part of your IAM policy. If you need more help
          in configuring IAM policies, you can read about them{" "}
          <DocsLink href="https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction_access-management.html">
            here
          </DocsLink>
          .
        </Text>
      </>
    ) : (
      <>
        <Text data-testid="generic-msg">
          Fides was unable to scan your infrastructure. Please ensure your
          credentials are accurate and inspect the error log below for more
          details.
        </Text>

        <ErrorLog message={error.message} />

        <Text>
          If this error does not clarify why scanning failed, please{" "}
          <DocsLink href={DOCS_URL_ISSUES}>create a new issue</DocsLink>.
        </Text>
      </>
    )}
  </Stack>
);

export default ScannerError;
