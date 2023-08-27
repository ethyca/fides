import React, { useState } from "react";
import {
  Modal,
  ModalBody,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Table,
  Tbody,
  Td,
  Thead,
  Tr,
} from "@fidesui/react";
import {
  SystemHistory,
  useGetSystemHistoryQuery,
} from "./system-history.slice";
import { SystemResponse } from "~/types/api/models/SystemResponse";

interface Props {
  system: SystemResponse;
}

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
    const { edited_by, before, after, created_at } = history;

    const fields = [];

    for (const [key, beforeValue] of Object.entries(before)) {
      const afterValue = after[key];
      if (JSON.stringify(beforeValue) !== JSON.stringify(afterValue)) {
        fields.push(key);
      }
    }

    if (fields.length === 0) {
      return null;
    }

    const lastField = fields.pop();
    const fieldList =
      fields.length > 0 ? (
        <>
          <b>{fields.join(", ")}</b>, and <b>{lastField}</b>
        </>
      ) : (
        <b>{lastField}</b>
      );

    // Convert UTC date to local time
    const date = new Date(created_at);
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

    return (
      <>
        <b>{edited_by}</b> updated the {fieldList} on {formattedDate} at{" "}
        {formattedTime}
      </>
    );
  };

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
              <b>System history</b>
            </Td>
          </Tr>
        </Thead>
        <Tbody>
          {systemHistories.map((history, index) => {
            const description = describeSystemChange(history);
            return (
              <Tr key={index} onClick={() => openModal(history)}>
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
      <Modal isOpen={isModalOpen} onClose={closeModal}>
        <ModalOverlay />
        <ModalContent style={{ width: "90%" }}>
          <ModalHeader>System History Details</ModalHeader>
          <ModalBody>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <div style={{ flex: "0 48%", marginRight: "4%" }}>
                <div style={{ fontWeight: "bold" }}>Before:</div>
                <pre>{JSON.stringify(selectedHistory?.before, null, 2)}</pre>
              </div>
              <div style={{ flex: "0 48%", marginLeft: "4%" }}>
                <div style={{ fontWeight: "bold" }}>After:</div>
                <pre>{JSON.stringify(selectedHistory?.after, null, 2)}</pre>
              </div>
            </div>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default SystemHistoryTable;
