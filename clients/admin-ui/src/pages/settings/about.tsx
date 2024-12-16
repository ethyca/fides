import {
  AntButton as Button,
  Box,
  Divider,
  Flex,
  Grid,
  Heading,
  Link,
  Text,
} from "fidesui";
import type { NextPage } from "next";

import { useFeatures } from "~/features/common/features";
import {
  FLAG_NAMES,
  useFlags,
} from "~/features/common/features/features.slice";
import { FlagControl } from "~/features/common/features/FlagControl";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const About: NextPage = () => {
  const features = useFeatures();
  const { flags, override, reset } = useFlags();

  return (
    <Layout title="About Fides">
      <PageHeader heading="About Fides">
        <Flex direction="column" gap={4}>
          <Box>
            <Text as="span" fontWeight="bold">
              Fides Core Version:{" "}
            </Text>
            <Text as="pre" display="inline">
              {features.version}
            </Text>
          </Box>

          {features.plusVersion ? (
            <Box>
              <Text as="span" fontWeight="bold">
                Fides Plus Version:{" "}
              </Text>
              <Text as="pre" display="inline">
                {features.plusVersion}
              </Text>
            </Box>
          ) : null}
          <Divider />
        </Flex>
      </PageHeader>

      <Flex alignItems="center" gap={4}>
        <Heading as="h2" fontSize="xl">
          Beta Features
        </Heading>
        <Button onClick={() => reset()}>Reset</Button>
      </Flex>
      <Grid
        gridTemplateColumns="1fr 2fr 6fr"
        gridColumnGap={4}
        gridRowGap={2}
        alignItems="center"
      >
        {FLAG_NAMES.map((flag) => (
          <FlagControl
            key={flag}
            flag={flag}
            value={flags[flag]}
            override={override}
          />
        ))}
      </Grid>

      <Box>
        <Text fontSize="sm">
          Please visit{" "}
          <Link
            color="complimentary.500"
            href="https://docs.ethyca.com"
            isExternal
          >
            docs.ethyca.com
          </Link>{" "}
          for more information on these features.
        </Text>

        <Text fontSize="sm">
          For questions and feedback, please join us at{" "}
          <Link
            color="complimentary.500"
            href="https://fidescommunity.slack.com"
            isExternal
          >
            fidescommunity.slack.com
          </Link>
          .
        </Text>
      </Box>
    </Layout>
  );
};
export default About;
