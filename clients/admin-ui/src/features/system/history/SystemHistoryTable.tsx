/* eslint-disable no-param-reassign */
import {
  AntButton as Button,
  Flex,
  Table,
  Tbody,
  Td,
  Text,
  Thead,
  Tr,
} from "fidesui";
import React, { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import NextArrow from "~/features/common/Icon/NextArrow";
import PrevArrow from "~/features/common/Icon/PrevArrow";
import {
  selectAllDictEntries,
  useGetSystemHistoryQuery,
} from "~/features/plus/plus.slice";
import { useGetAllSystemsQuery } from "~/features/system/system.slice";
import { SystemHistoryResponse } from "~/types/api";
import { SystemResponse } from "~/types/api/models/SystemResponse";

import {
  alignPrivacyDeclarationCustomFields,
  alignPrivacyDeclarations,
  alignSystemCustomFields,
  assignSystemNames,
  assignVendorLabels,
  describeSystemChange,
  formatDateAndTime,
} from "./helpers";
import SystemHistoryModal from "./modal/SystemHistoryModal";

interface Props {
  system: SystemResponse;
}

const ITEMS_PER_PAGE = 10;

const SystemHistoryTable = ({ system }: Props) => {
  const [currentPage, setCurrentPage] = useState(1);
  const { data } = useGetSystemHistoryQuery({
    system_key: system.fides_key,
    page: currentPage,
    size: ITEMS_PER_PAGE,
  });
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedHistory, setSelectedHistory] =
    useState<SystemHistoryResponse | null>(null);
  const dictionaryOptions = useAppSelector(selectAllDictEntries);
  const { data: systems = [] } = useGetAllSystemsQuery();

  const systemHistories = data?.items || [];

  const openModal = (history: SystemHistoryResponse) => {
    // Align the before and after privacy declaration lists so they have the same number of entries
    history = alignPrivacyDeclarations(history);
    // Look up the vendor labels from the vendor IDs
    history = assignVendorLabels(history, dictionaryOptions);
    // Look up the system names for the source and destination fides_keys
    history = assignSystemNames(history, systems);
    // Align custom fields
    history = alignSystemCustomFields(history);
    history = alignPrivacyDeclarationCustomFields(history);

    setSelectedHistory(history);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedHistory(null);
  };

  const { formattedTime, formattedDate } = formatDateAndTime(system.created_at);

  const totalPages =
    data && data.total ? Math.ceil(data.total / ITEMS_PER_PAGE) : 0;

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <>
      <Table ml="24px">
        <Thead>
          <Tr>
            <Td
              p="16px"
              fontSize="12px"
              border="1px solid #E2E8F0"
              background="#F7FAFC"
            >
              System created on {formattedDate} at {formattedTime}
            </Td>
          </Tr>
        </Thead>
        <Tbody>
          {systemHistories.map((history, index) => {
            const description = describeSystemChange(history);
            if (description) {
              return (
                <Tr
                  // eslint-disable-next-line react/no-array-index-key
                  key={index}
                  onClick={() => openModal(history)}
                  style={{ cursor: "pointer" }}
                >
                  <Td
                    pt="10px"
                    pb="10px"
                    pl="16px"
                    fontSize="12px"
                    border="1px solid #E2E8F0"
                  >
                    {description}
                  </Td>
                </Tr>
              );
            }
            return null;
          })}
        </Tbody>
      </Table>
      {(data?.total || 0) > 10 && (
        <Flex
          alignItems="center"
          justifyContent="flex-start"
          marginTop="12px"
          marginLeft="24px"
        >
          <Text fontSize="xs" lineHeight={4} fontWeight="600" paddingX={2}>
            {(currentPage - 1) * ITEMS_PER_PAGE + 1} -{" "}
            {Math.min(currentPage * ITEMS_PER_PAGE, data?.total || 0)} of{" "}
            {data?.total || 0}
          </Text>
          <Button
            size="small"
            className="mr-2"
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            icon={<PrevArrow />}
          />
          <Button
            size="small"
            onClick={handleNextPage}
            disabled={currentPage === totalPages || totalPages === 0}
            icon={<NextArrow />}
          />
        </Flex>
      )}
      <SystemHistoryModal
        selectedHistory={selectedHistory!}
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </>
  );
};

export default SystemHistoryTable;
