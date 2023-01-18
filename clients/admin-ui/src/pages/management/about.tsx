import {
  Box,
  Button,
  Divider,
  Flex,
  Grid,
  Heading,
  Link,
  Text,
} from "@fidesui/react";
import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import {
  FLAG_NAMES,
  useFlags,
} from "~/features/common/features/features.slice";
import { FlagControl } from "~/features/common/features/FlagControl";
import Layout from "~/features/common/Layout";

const About: NextPage = () => {
  const features = useFeatures();
  const { flags, defaults, override, reset } = useFlags();

  return (
    <Layout title="About Fides">
      <Flex direction="column" gap={4}>
        <Heading fontSize="2xl">About Fides</Heading>

        <Box>
          <Text as="span" fontWeight="bold">
            Version:{" "}
          </Text>
          <Text as="pre" display="inline">
            {features.version}
          </Text>
        </Box>

        <Divider />

        <Grid gridTemplateColumns="1fr 1fr 3fr">
          <Heading as="h2" fontSize="xl">
            Beta Features
          </Heading>

          <Box mb={2}>
            <Button size="sm" onClick={() => reset()}>
              Reset
            </Button>
          </Box>

          <Box />

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

        <Box>
          <Text fontSize="sm">
            Please visit docs.ethyca.com for more information on these features.
          </Text>

          <Text fontSize="sm">
            For questions and feedback, please join us at{" "}
            <Link href="fidescommunity.slack.com" isExternal>
              fidescommunity.slack.com
            </Link>
          </Text>
        </Box>
      </Flex>
    </Layout>
  );
};
export default About;
