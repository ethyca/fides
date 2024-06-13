/* eslint-disable @typescript-eslint/no-use-before-define */
import { Badge, Box, Button, Flex, Select, Spinner, Text } from "fidesui";
import { Formik } from "formik";
import { M } from "msw/lib/glossary-de6278a9";
import { NextPage } from "next";
import { useState } from "react";

import DataTabsHeader from "~/features/common/DataTabsHeader";
import FixedLayout from "~/features/common/FixedLayout";
import FormSection from "~/features/common/form/FormSection";
import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import PageHeader from "~/features/common/PageHeader";
import { useGetAllPropertiesQuery } from "~/features/properties";

const MessagingPage: NextPage = () => {
  const [selectedProperty, setSelectedProperty] = useState<string | undefined>(
    undefined
  );
  const [selectedTemplate, setSelectedTemplate] = useState<string | undefined>(
    undefined
  );

  const {
    isFetching,
    isLoading,
    data: properties,
  } = useGetAllPropertiesQuery({
    page: 1,
    size: 50,
  });

  const templates = [
    { title: "Subject identity verification", state: "CUSTOM" },
    { title: "Privacy request received", state: "CUSTOM" },
    { title: "Privacy request approved", state: "DEFAULT" },
    { title: "Privacy request denied", state: "DEFAULT" },
    { title: "Access request completed", state: "CUSTOM" },
    { title: "Erasure request completed", state: "DISABLED" },
  ];

  console.log("properties", properties);

  const isEditorEnabled = selectedProperty && selectedTemplate;

  return (
    <FixedLayout
      title="Messaging"
      mainProps={{
        padding: "0 40px 10px",
      }}
    >
      <PageHeader breadcrumbs={[{ title: "Messaging" }]}>
        <Text fontWeight={500} color="gray.700">
          Configure Fides messaging.
        </Text>
      </PageHeader>

      <DataTabsHeader
        data={[{ label: "Email templates" }]}
        borderBottomWidth={1}
      />

      {isLoading && <Spinner />}
      {!isLoading && (
        <Flex height={800}>
          <Box
            flexShrink={0}
            flexGrow={0}
            borderRightWidth={1}
            width={350}
            py={2}
            px={3}
            pr={8}
          >
            <Flex height="full" direction="column" marginBottom={2}>
              <Box flex={1} borderBottomWidth={1}>
                <StepHeading step={1} title="Select a property" />
                <Select
                  value={selectedProperty}
                  onChange={(e) => setSelectedProperty(e.target.value)}
                >
                  <option value="">&nbsp;</option>
                  {properties &&
                    properties.items.map((property) => (
                      <option key={property.name} value={property.id}>
                        {property.name}
                      </option>
                    ))}
                </Select>
              </Box>
              <Box flex={1} pt={3}>
                <StepHeading step={2} title="Select an email template" />
                {/* <Select
                  disabled={!selectedProperty}
                  value={selectedTemplate}
                  onChange={(e) => setSelectedTemplate(e.target.value)}
                >
                  <option value="">&nbsp;</option>
                  {templates.map((template) => (
                    <option key={template.title} value={template.title}>
                      {template.title} ({template.state})
                    </option>
                  ))}
                </Select> */}

                {selectedProperty && (
                  <Box>
                    {templates.map((template) => (
                      <Flex
                        key={template.title}
                        justify="space-between"
                        align="center"
                        borderWidth={1}
                        p={2}
                        pl={3}
                        borderColor={
                          selectedTemplate === template.title
                            ? "complimentary.500"
                            : "gray.200"
                        }
                        mb={2}
                        cursor="pointer"
                        onClick={() => setSelectedTemplate(template.title)}
                        borderRadius={10}
                      >
                        <Text
                          key={template.title}
                          fontSize="medium"
                          color="gray.500"
                        >
                          {template.title}
                        </Text>
                        <Badge
                          colorScheme={
                            template.state === "CUSTOM" ? "green" : "gray"
                          }
                        >
                          {template.state}
                        </Badge>
                      </Flex>
                    ))}
                  </Box>
                )}
              </Box>
            </Flex>
          </Box>
          <Box flex={1} borderRightWidth={1} py={2} px={3}>
            {isEditorEnabled && (
              <>
                <StepHeading step={3} title="Edit the template" />
                <Formik
                  initialValues={{
                    messagesubject: selectedTemplate,
                    messagebody:
                      "Lorem ipsum dolor sit, amet consectetur adipisicing elit. Quasi minima maxime, quas laboriosam delectus dignissimos molestias doloribus sint ",
                  }}
                >
                  <FormSection title={selectedTemplate}>
                    <CustomTextInput
                      label="Message subject"
                      name="messagesubject"
                      variant="stacked"
                    />
                    <CustomTextArea
                      label="Message body"
                      name="messagebody"
                      variant="stacked"
                      resize
                    />
                  </FormSection>
                </Formik>
                <Flex justifyContent="right" width="100%" paddingTop={2}>
                  <Button
                    size="sm"
                    type="submit"
                    colorScheme="primary"
                    isLoading={isLoading}
                  >
                    Save
                  </Button>
                </Flex>
              </>
            )}
          </Box>
          <Box flex={1} py={2} px={3}>
            {isEditorEnabled && <StepHeading title="Preview" />}
          </Box>
        </Flex>
      )}
    </FixedLayout>
  );
};

const StepHeading = ({ step, title }: { step: number; title: string }) => (
  <Flex alignItems="baseline">
    {step && (
      <Text
        fontWeight={700}
        color="gray.700"
        fontSize="x-large"
        marginRight={2}
        marginBottom={2}
      >
        {step}.
      </Text>
    )}
    <Text fontWeight={500} fontSize="larger">
      {title}
    </Text>
  </Flex>
);

export default MessagingPage;
