import {
  Box,
  Button,
  Heading,
  Spinner,
  Center,
  Flex,
  Link,
  Text,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import { useState } from "react";
import { CustomTextInput } from "~/features/common/form/inputs";
import {
  useLazyGetScanPiiQuery,
  useLazyGetScanStatsQuery,
} from "~/pages/scan-codebase/scan-codebase.slice";

import Layout from "~/features/common/Layout";
// import CheckboxGrid from "./CheckboxGrid";
// import DonutChart from "./DonutChart";
import GitHubCodeViewer from "./GitHubCodeViewer";
import DocsLink from "~/features/common/DocsLink";

type StatFormValues = {
  url: string;
};
const initialStatFormValues = {
  url: "",
};

enum Views {
  Intial = "1",
  Stats = "2",
  Scan = "3",
}

const ScanCodebase: NextPage = () => {
  const [statsTrigger, { isLoading: isStatsLoading, data: statsData }] =
    useLazyGetScanStatsQuery();
  const [scanTrigger, { isLoading: isScanLoading }] = useLazyGetScanPiiQuery();
  const [codebaseId, setCodebaseId] = useState<string>();
  const [scan, setScan] = useState<Scan[]>([]);
  const [stats, setStats] = useState<string[]>([]);
  const [currentView, setCurrentView] = useState<Views>(Views.Intial);

  const handleSubmit = async (values: StatFormValues) => {
    try {
      const payload = await statsTrigger({ url: values.url }).unwrap();
      const response = await scanTrigger({ id: payload.instance_id }).unwrap();

      setScan(response.flatMap((s) => s.finding_urls));
      // setCodebaseId(payload.instance_id);
      setCurrentView(Views.Scan);
    } catch (error) {
      console.error(error);
    }
  };

  const startScan = async () => {
    try {
      if (codebaseId) {
        const response = await scanTrigger({ id: codebaseId }).unwrap();
        setCurrentView(Views.Scan);
        setScan(response.flatMap((s) => s.finding_urls));
      }
    } catch (error) {
      console.error(error);
    }
  };

  const piiTags = [
    "Name",
    "Email",
    "Phone number",
    "Driver's license number",
    "Payment information",
    "Shipping information",
    "Date of birth",
    "Healthcare or medical information",
    "IP address",
    "Usernames and passwords",
    "Race or ethnicity",
    "Religious beliefs",
  ];
  const fileData = [
    { fileType: "Python", percentage: 57 },
    { fileType: "Typescript", percentage: 24 },
    { fileType: "HTML", percentage: 13 },
    { fileType: "CSS", percentage: 6 },
  ];
  const githubUrl =
    "https://raw.githubusercontent.com/ethyca/fides/d84f6bde4dcd1fe595bae3f05efff0a0c9984cd1/src/fides/api/main.py";
  const githubUrl2 =
    "https://raw.githubusercontent.com/ethyca/fides/d84f6bde4dcd1fe595bae3f05efff0a0c9984cd1/clients/admin-ui/src/home/HomeBanner.tsx";
  return (
    <Layout title="Scan codebase">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        PII Scanner
      </Heading>
      <Text fontSize="sm" mt={2} mb={8} width={{ base: "100%", lg: "50%" }}>
        {currentView === Views.Intial ? "Enter a Github repo URL to have all of the files check for PII and PII usage": "The results below are probable instances of PII and PII usage"}
      </Text>
      <Box maxW="800px">
      {(isStatsLoading || isScanLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {currentView === Views.Intial && !(isStatsLoading || isScanLoading) ? (
        <Formik initialValues={initialStatFormValues} onSubmit={handleSubmit}>
          {({ isSubmitting, dirty, isValid }) => (
            <Form>
              <Box marginTop={3}>
                <Heading mb={2} fontSize="md" fontWeight="500">
                    Github URL
                </Heading>
                <CustomTextInput
                  name="url"
                  variant="stacked"
                />
              </Box>
              <Flex marginTop={6} justifyContent="flex-start">
                <Button
                  textAlign="right"
                  type="submit"
                  disabled={!dirty || !isValid}
                  colorScheme="primary"
                  isLoading={isSubmitting}
                  size="sm"
                >
                  Start Scan
                </Button>
              </Flex>
            </Form>
          )}
        </Formik>
      ) : null}
      {currentView === Views.Stats && !(isStatsLoading || isScanLoading) ? (
        <>
          {/*<DonutChart data={fileData} />*/}
          {/* <CheckboxGrid options={piiTags} /> */}
          <Flex marginTop={6} justifyContent="flex-end">
            <Button
              textAlign="right"
              colorScheme="primary"
              isLoading={isScanLoading}
              onClick={startScan}
              size="sm"
            >
              Start Scan
            </Button>
          </Flex>
        </>
      ) : null}
      {currentView === Views.Scan && !(isStatsLoading || isScanLoading) ? (
        <>
          {scan.map((s) => (
            <Box
              border="solid 2px"
              borderColor="gray.200"
              borderRadius="4px"
              my={2}
              p={2}
            >
              <GitHubCodeViewer
                key={s.raw_url}
                url={s.raw_url}
                full_url={s.full_url}
                language={s.file_type}
              />
              <Text
                color="complimentary.500"
                textDecoration="underline"
                cursor="pointer"
                fontSize="sm"
                onClick={() => {
                  window.open(s.full_url);
                }}
              >
                {s.full_url}{" "}
              </Text>
            </Box>
          ))}
        </>
      ) : null}
    </Box>
    </Layout>
  );
};

export default ScanCodebase;
