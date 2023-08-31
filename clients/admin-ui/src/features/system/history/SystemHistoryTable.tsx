import {
  Badge,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Spacer,
  Stack,
  Table,
  Tbody,
  Td,
  Thead,
  Tr,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import _ from "lodash";
import React, { useState } from "react";

import { SystemResponse } from "~/types/api/models/SystemResponse";

import SelectedHistoryProvider from "./SelectedHistoryContext";
import {
  SystemHistory,
  useGetSystemHistoryQuery,
} from "./system-history.slice";
import SystemDataGroup from "./SystemDataGroup";
import SystemDataTags from "./SystemDataTags";
import SystemDataTextField from "./SystemDataTextField";

interface Props {
  system: SystemResponse;
}

// Helper function to format date and time
const formatDateAndTime = (dateString: string) => {
  const date = new Date(dateString);
  const userLocale = navigator.language;

  const timeOptions = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    timeZoneName: "short",
  };

  const dateOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };

  const formattedTime = date.toLocaleTimeString(userLocale, timeOptions);
  const formattedDate = date.toLocaleDateString(userLocale, dateOptions);

  return { formattedTime, formattedDate };
};

const getBadges = (before, after) => {
  const badges = [];
  const specialFields = new Set(["egress", "ingress", "privacy_declarations"]);

  if (before.egress || after.egress || before.ingress || after.ingress) {
    badges.push("Data Flow");
  }

  if (before.privacy_declarations || after.privacy_declarations) {
    badges.push("Data Uses");
  }

  const hasOtherFields = [...Object.keys(before), ...Object.keys(after)].some(
    (key) => !specialFields.has(key)
  );
  if (hasOtherFields) {
    badges.unshift("System Information");
  }

  return badges;
};

const SystemHistoryTable = ({ system }: Props) => {
  // Fetch system history data
  const { data } = useGetSystemHistoryQuery({
    system_key: system.fides_key,
  });
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedHistory, setSelectedHistory] = useState<SystemHistory | null>(
    null
  );

  const systemHistories = data?.items || [];

  const openModal = (history: SystemHistory) => {
    setSelectedHistory(history);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedHistory(null);
  };

  const describeSystemChange = (history: SystemHistory) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { edited_by, before, after, created_at } = history;

    const uniqueKeys = new Set([...Object.keys(before), ...Object.keys(after)]);

    const addedFields = [];
    const removedFields = [];
    const changedFields = [];

    Array.from(uniqueKeys).forEach((key) => {
      const beforeValue = before[key];
      const afterValue = after[key];

      if (Array.isArray(beforeValue) && Array.isArray(afterValue)) {
        if (beforeValue.length < afterValue.length) {
          addedFields.push(key);
        } else if (beforeValue.length > afterValue.length) {
          removedFields.push(key);
        } else if (JSON.stringify(beforeValue) !== JSON.stringify(afterValue)) {
          changedFields.push(key);
        }
      } else if (_.isEmpty(beforeValue) && !_.isEmpty(afterValue)) {
        addedFields.push(key);
      } else if (_.isEmpty(afterValue) && !_.isEmpty(beforeValue)) {
        removedFields.push(key);
      } else if (JSON.stringify(beforeValue) !== JSON.stringify(afterValue)) {
        changedFields.push(key);
      }
    });

    const changeDescriptions = [];

    if (addedFields.length > 0) {
      // eslint-disable-next-line react/jsx-key
      changeDescriptions.push(["added ", <b>{addedFields.join(", ")}</b>]);
    }

    if (removedFields.length > 0) {
      // eslint-disable-next-line react/jsx-key
      changeDescriptions.push(["removed ", <b>{removedFields.join(", ")}</b>]);
    }

    if (changedFields.length > 0) {
      // eslint-disable-next-line react/jsx-key
      changeDescriptions.push(["changed ", <b>{changedFields.join(", ")}</b>]);
    }

    if (changeDescriptions.length === 0) {
      return null;
    }

    const lastDescription = changeDescriptions.pop();

    const descriptionList =
      changeDescriptions.length > 0 ? (
        <>
          {changeDescriptions.map((desc, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <React.Fragment key={i}>
              {desc}
              {i < changeDescriptions.length - 1 ? ", " : ""}
            </React.Fragment>
          ))}
          {changeDescriptions.length >= 2 ? ", and " : " and "}
          {lastDescription}
        </>
      ) : (
        lastDescription
      );

    const { formattedTime, formattedDate } = formatDateAndTime(created_at);

    return (
      <>
        <b>{edited_by}</b> {descriptionList} on {formattedDate} at{" "}
        {formattedTime}
      </>
    );
  };

  const { formattedTime, formattedDate } = formatDateAndTime(system.created_at);

  return (
    <>
      <Table style={{ marginLeft: "24px" }}>
        <Thead>
          <Tr>
            <Td
              style={{
                paddingTop: 16,
                paddingBottom: 16,
                paddingLeft: 16,
                fontSize: 12,
                borderTop: "1px solid #E2E8F0",
                borderLeft: "1px solid #E2E8F0",
                borderRight: "1px solid #E2E8F0",
                background: "#F7FAFC",
              }}
            >
              System created
              {system.created_by && (
                <>
                  {" "}
                  by <b>{system.created_by}</b>{" "}
                </>
              )}
              on {formattedDate} at {formattedTime}
            </Td>
          </Tr>
        </Thead>
        <Tbody>
          {systemHistories.map((history, index) => {
            const description = describeSystemChange(history);
            return (
              <Tr
                // eslint-disable-next-line react/no-array-index-key
                key={index}
                onClick={() => openModal(history)}
                style={{ cursor: "pointer" }}
              >
                <Td
                  style={{
                    paddingTop: 10,
                    paddingBottom: 10,
                    paddingLeft: 16,
                    fontSize: 12,
                    borderLeft: "1px solid #E2E8F0",
                    borderRight: "1px solid #E2E8F0",
                  }}
                >
                  {description}
                </Td>
              </Tr>
            );
          })}
        </Tbody>
      </Table>
      <Modal isOpen={isModalOpen} onClose={closeModal} size="3xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader
            style={{
              backgroundColor: "#F7FAFC",
              borderTopLeftRadius: "8px",
              borderTopRightRadius: "8px",
              borderBottom: "1px solid #E2E8F0",
            }}
          >
            <Heading size="xs">
              <span style={{ verticalAlign: "middle" }}>Diff review</span>
              {selectedHistory && (
                <>
                  {getBadges(selectedHistory.before, selectedHistory.after).map(
                    (badge, index) => (
                      <Badge
                        // eslint-disable-next-line react/no-array-index-key
                        key={index}
                        marginLeft="8px"
                        fontSize="10px"
                        padding="0px 4px"
                        variant="solid"
                        lineHeight="18px"
                        height="18px"
                        backgroundColor="#718096"
                        borderRadius="2px"
                      >
                        {badge}
                      </Badge>
                    )
                  )}
                </>
              )}
            </Heading>
            <>
              <Spacer />
              <ModalCloseButton />
            </>
          </ModalHeader>
          <ModalBody paddingTop={0} paddingBottom={6}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
              }}
            >
              <div
                style={{
                  flex: "0 50%",
                  marginRight: "12px",
                }}
              >
                <SelectedHistoryProvider
                  selectedHistory={selectedHistory}
                  formType="before"
                >
                  <Formik
                    initialValues={selectedHistory?.before}
                    enableReinitialize
                  >
                    {() => (
                      <Form>
                        <Stack>
                          <SystemDataGroup heading="System details">
                            <SystemDataTextField
                              id="name"
                              name="name"
                              label="System name"
                              variant="stacked"
                              tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                            />
                            <SystemDataTextField
                              id="description"
                              name="description"
                              label="Description"
                              variant="stacked"
                              tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                            />
                            <SystemDataTags
                              id="tags"
                              name="tags"
                              label="System Tags"
                              variant="stacked"
                              tooltip="Are there any tags to associate with this system?"
                            />
                          </SystemDataGroup>
                          <SystemDataGroup heading="Dataset reference">
                            <SystemDataTags
                              id="dataset_references"
                              name="dataset_references"
                              label="Dataset references"
                              variant="stacked"
                              tooltip="Is there a dataset configured for this system"
                            />
                          </SystemDataGroup>
                          <SystemDataGroup heading="Administrative properties">
                            <SystemDataTextField
                              label="Data stewards"
                              name="data_stewards"
                              tooltip="Who are the stewards assigned to the system?"
                              variant="stacked"
                            />
                            <SystemDataTextField
                              id="legal_name"
                              name="legal_name"
                              label="Legal name"
                              tooltip="What is the legal name of the business?"
                              variant="stacked"
                            />
                            <SystemDataTextField
                              label="Department"
                              name="administrating_department"
                              tooltip="Which department is concerned with this system?"
                              variant="stacked"
                            />
                            <SystemDataTags
                              label="Responsibility"
                              name="responsibility"
                              variant="stacked"
                              tooltip="What is the role of the business with regard to data processing?"
                            />
                          </SystemDataGroup>
                          <SystemDataGroup heading="Data use declaration">
                            <SystemDataTextField
                              id="privacy_declarations[0].name"
                              label="Declaration name (optional)"
                              name="privacy_declarations[0].name"
                              tooltip="Would you like to append anything to the system name?"
                              variant="stacked"
                            />
                          </SystemDataGroup>
                        </Stack>
                      </Form>
                    )}
                  </Formik>
                </SelectedHistoryProvider>
              </div>
              <div
                style={{
                  flex: "0 50%",
                  marginLeft: "12px",
                }}
              >
                <SelectedHistoryProvider
                  selectedHistory={selectedHistory}
                  formType="after"
                >
                  <Formik
                    initialValues={selectedHistory?.after}
                    enableReinitialize
                  >
                    {() => (
                      <Form>
                        <Stack spacing={0}>
                          <SystemDataGroup heading="System details">
                            <SystemDataTextField
                              id="name"
                              name="name"
                              label="System name"
                              variant="stacked"
                              tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                            />
                            <SystemDataTextField
                              id="description"
                              name="description"
                              label="Description"
                              variant="stacked"
                              tooltip="Give the system a unique, and relevant name for reporting purposes. e.g. “Email Data Warehouse”"
                            />
                            <SystemDataTags
                              id="tags"
                              name="tags"
                              label="System Tags"
                              variant="stacked"
                              tooltip="Are there any tags to associate with this system?"
                              isMulti
                            />
                          </SystemDataGroup>
                          <SystemDataGroup heading="Dataset reference">
                            <SystemDataTags
                              id="dataset_references"
                              name="dataset_references"
                              label="Dataset references"
                              variant="stacked"
                              tooltip="Is there a dataset configured for this system"
                            />
                          </SystemDataGroup>
                          <SystemDataGroup heading="Administrative properties">
                            <SystemDataTextField
                              label="Data stewards"
                              name="data_stewards"
                              tooltip="Who are the stewards assigned to the system?"
                              variant="stacked"
                            />
                            <SystemDataTextField
                              id="legal_name"
                              name="legal_name"
                              label="Legal name"
                              tooltip="What is the legal name of the business?"
                              variant="stacked"
                            />
                            <SystemDataTextField
                              label="Department"
                              name="administrating_department"
                              tooltip="Which department is concerned with this system?"
                              variant="stacked"
                            />
                            <SystemDataTags
                              label="Responsibility"
                              name="responsibility"
                              variant="stacked"
                              tooltip="What is the role of the business with regard to data processing?"
                            />
                          </SystemDataGroup>
                          <SystemDataGroup heading="Data use declaration">
                            <SystemDataTextField
                              id="privacy_declarations[0].name"
                              label="Declaration name (optional)"
                              name="privacy_declarations[0].name"
                              tooltip="Would you like to append anything to the system name?"
                              variant="stacked"
                            />
                          </SystemDataGroup>
                        </Stack>
                      </Form>
                    )}
                  </Formik>
                </SelectedHistoryProvider>
              </div>
            </div>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default SystemHistoryTable;
