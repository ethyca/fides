import {
  Box,
  GreenCheckCircleIcon,
  Heading,
  HStack,
  Stack,
  AntButton as Button,
  AntSelect as Select,
  Text,
  Textarea,
  VStack,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";
import { useAppDispatch } from "~/app/hooks";
import ClipboardButton from "~/features/common/ClipboardButton";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { Editor } from "~/features/common/yaml/helpers";
import { ExportFormat } from "~/features/datamap/constants";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";

const SubSystemPage: NextPage = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();

  let systemId = "";
  if (router.query.id) {
    systemId = Array.isArray(router.query.id)
      ? router.query.id[0]
      : router.query.id;
  }

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });

  useEffect(() => {
    dispatch(setActiveSystem(system));
  }, [system, dispatch]);

  if (isLoading) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  return (
    <Layout
      title="System inventory"
      mainProps={{
        paddingTop: 0,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <PageHeader
        breadcrumbs={[
          { title: "System inventory", link: SYSTEM_ROUTE },
          {
            title: system?.name || "",
            link: `/systems/configure/${systemId}#integrations`,
          },
          { title: "Test datasets" },
        ]}
        isSticky
      >
        <Box position="relative">
          {/* Add your sub-page header content here */}
        </Box>
      </PageHeader>
      <HStack
        alignItems="stretch"
        flex="1"
        minHeight="0"
        spacing="4"
        padding="4 4 4 0"
      >
        <VStack alignItems="stretch" flex="1" maxWidth="70vw" maxHeight="100vh">
          <Heading
            as="h3"
            size="sm"
            display="flex"
            alignItems="center"
            justifyContent="space-between"
          >
            <HStack>
              <Text>Edit dataset: </Text>
              <Select
                id="format"
                data-testid="export-format-select"
                options={[
                  {
                    value: ExportFormat.csv,
                    label: "postgres_example_test_dataset",
                  },
                  {
                    value: ExportFormat.xlsx,
                    label: "postgres_example_test_dataset",
                  },
                ]}
                className="w-64"
              />
              <ClipboardButton copyText="hello" />
            </HStack>
            <HStack spacing={2}>
              <Button htmlType="submit" size="small" data-testid="save-btn">
                Refresh
              </Button>
              <Button htmlType="submit" size="small">
                Save
              </Button>
            </HStack>
          </Heading>
          <Stack
            border="1px solid"
            borderColor="gray.200"
            borderRadius="md"
            justifyContent="space-between"
            py={4}
            pr={4}
            data-testid="empty-state"
            height="100vh"
          >
            <Editor
              defaultLanguage="yaml"
              defaultValue="test"
              height="100%"
              onChange={() => {}}
              onMount={() => {}}
              options={{
                fontFamily: "Menlo",
                fontSize: 13,
                minimap: {
                  enabled: false,
                },
                readOnly: false,
                hideCursorInOverviewRuler: true,
                overviewRulerBorder: false,
                scrollBeyondLastLine: false,
              }}
              theme="light"
            />
          </Stack>
          <Stack
            backgroundColor="gray.50"
            border="1px solid"
            borderColor="green.500"
            borderRadius="md"
            justifyContent="space-between"
            py={2}
            px={4}
          >
            <Text fontSize="sm">
              <GreenCheckCircleIcon /> Dataset is reachable via the <b>email</b>{" "}
              identity
            </Text>
          </Stack>
        </VStack>
        <VStack alignItems="stretch" flex="1" maxWidth="70vw" minHeight="0">
          <Heading
            as="h3"
            size="sm"
            display="flex"
            alignItems="center"
            justifyContent="space-between"
          >
            <HStack>
              <Text>Test inputs (identities and references)</Text>
              <ClipboardButton copyText="hello" />
            </HStack>
            <Button
              htmlType="submit"
              size="small"
              type="primary"
              data-testid="save-btn"
            >
              Run
            </Button>
          </Heading>
          <Textarea
            size="sm"
            focusBorderColor="primary.600"
            color="gray.800"
            isDisabled={false}
            height="100%"
            defaultValue={JSON.stringify(
              { email: "user@example.com" },
              null,
              2,
            )}
          />
          <Heading as="h3" size="sm">
            SQL queries <ClipboardButton copyText="hello" />
          </Heading>
          <Textarea
            isReadOnly
            size="sm"
            focusBorderColor="primary.600"
            color="gray.800"
            isDisabled={false}
            height="100%"
            defaultValue={
              "SELECT * FROM customer WHERE email='user@example.com'"
            }
          />
          <Heading as="h3" size="sm">
            Test results <ClipboardButton copyText="hello" />
          </Heading>
          <Textarea
            isReadOnly
            size="sm"
            focusBorderColor="primary.600"
            color="gray.800"
            isDisabled={false}
            height="100%"
            defaultValue={JSON.stringify(
              { customer: [{ first_name: "Test" }] },
              null,
            )}
          />
        </VStack>
      </HStack>
    </Layout>
  );
};

export default SubSystemPage;
