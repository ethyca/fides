import {
  Button,
  Flex,
  Table,
  Tbody,
  Td,
  Text,
  Thead,
  Tr,
} from "@fidesui/react";
import _ from "lodash";
import React, { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import NextArrow from "~/features/common/Icon/NextArrow";
import PrevArrow from "~/features/common/Icon/PrevArrow";
import {
  DictOption,
  selectAllDictEntries,
  useGetSystemHistoryQuery,
} from "~/features/plus/plus.slice";
import { PrivacyDeclaration, SystemHistoryResponse } from "~/types/api";
import { SystemResponse } from "~/types/api/models/SystemResponse";

import SystemHistoryModal from "./modal/SystemHistoryModal";

interface Props {
  system: SystemResponse;
}

// Helper function to format date and time
const formatDateAndTime = (dateString: string) => {
  const date = new Date(dateString);
  const userLocale = navigator.language;

  const timeOptions: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
    timeZoneName: "short",
  };

  const dateOptions: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "long",
    day: "numeric",
  };

  const formattedTime = date.toLocaleTimeString(userLocale, timeOptions);
  const formattedDate = date.toLocaleDateString(userLocale, dateOptions);

  return { formattedTime, formattedDate };
};

function alignArrays(
  before: PrivacyDeclaration[],
  after: PrivacyDeclaration[]
) {
  const allNames = new Set([...before, ...after].map((item) => item.data_use));
  const alignedBefore: PrivacyDeclaration[] = [];
  const alignedAfter: PrivacyDeclaration[] = [];

  allNames.forEach((data_use) => {
    const firstItem = before.find((item) => item.data_use === data_use) || {
      data_use: "",
      data_categories: [],
    };
    const secondItem = after.find((item) => item.data_use === data_use) || {
      data_use: "",
      data_categories: [],
    };
    alignedBefore.push(firstItem);
    alignedAfter.push(secondItem);
  });

  return [alignedBefore, alignedAfter];
}

const lookupVendorLabel = (vendor_id: string, options: DictOption[]) =>
  options.find((option) => option.value === vendor_id)?.label ?? vendor_id;

const itemsPerPage = 10;

const SystemHistoryTable = ({ system }: Props) => {
  const [currentPage, setCurrentPage] = useState(1);
  const { data } = useGetSystemHistoryQuery({
    system_key: system.fides_key,
    page: currentPage,
    size: itemsPerPage,
  });
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedHistory, setSelectedHistory] =
    useState<SystemHistoryResponse | null>(null);
  const dictionaryOptions = useAppSelector(selectAllDictEntries);

  const systemHistories = data?.items || [];

  const openModal = (history: SystemHistoryResponse) => {
    // Align the privacy_declarations arrays
    const beforePrivacyDeclarations =
      history?.before?.privacy_declarations || [];
    const afterPrivacyDeclarations = history?.after?.privacy_declarations || [];
    const [alignedBefore, alignedAfter] = alignArrays(
      beforePrivacyDeclarations,
      afterPrivacyDeclarations
    );

    // Create new initialValues objects with the aligned arrays
    const alignedBeforeInitialValues = {
      ...history?.before,
      privacy_declarations: alignedBefore,
    };
    const alignedAfterInitialValues = {
      ...history?.after,
      privacy_declarations: alignedAfter,
    };

    if (dictionaryOptions) {
      alignedBeforeInitialValues.vendor_id = lookupVendorLabel(
        alignedBeforeInitialValues.vendor_id,
        dictionaryOptions
      );
      alignedAfterInitialValues.vendor_id = lookupVendorLabel(
        alignedAfterInitialValues.vendor_id,
        dictionaryOptions
      );
    }

    setSelectedHistory({
      before: alignedBeforeInitialValues,
      after: alignedAfterInitialValues,
      edited_by: history.edited_by,
      system_id: history.system_id,
      created_at: history.created_at,
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedHistory(null);
  };

  const describeSystemChange = (history: SystemHistoryResponse) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { edited_by, before, after, created_at } = history;

    const uniqueKeys = new Set([...Object.keys(before), ...Object.keys(after)]);

    const addedFields: string[] = [];
    const removedFields: string[] = [];
    const changedFields: string[] = [];

    Array.from(uniqueKeys).forEach((key) => {
      // @ts-ignore
      const beforeValue = before[key];
      // @ts-ignore
      const afterValue = after[key];

      // Handle booleans separately
      if (typeof beforeValue === "boolean" || typeof afterValue === "boolean") {
        if (beforeValue !== afterValue) {
          changedFields.push(key);
        }
        return;
      }

      // Handle numbers separately
      if (typeof beforeValue === "number" || typeof afterValue === "number") {
        if (beforeValue !== afterValue) {
          changedFields.push(key);
        }
        return;
      }

      // If both values are null or empty, skip
      if (
        (_.isNil(beforeValue) || _.isEmpty(beforeValue)) &&
        (_.isNil(afterValue) || _.isEmpty(afterValue))
      ) {
        return;
      }

      // For all other types
      if (!_.isEqual(beforeValue, afterValue)) {
        if (_.isNil(beforeValue) || _.isEmpty(beforeValue)) {
          addedFields.push(key);
        } else if (_.isNil(afterValue) || _.isEmpty(afterValue)) {
          removedFields.push(key);
        } else {
          changedFields.push(key);
        }
      }
    });

    const changeDescriptions: Array<[string, JSX.Element]> = [];

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

  const totalPages = data ? Math.ceil(data.total / itemsPerPage) : 0;

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
              System created
              {system.created_by && (
                <>
                  {" "}
                  by <b>{system.created_by}</b>{" "}
                </>
              )}{" "}
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
            {(currentPage - 1) * itemsPerPage + 1} -{" "}
            {Math.min(currentPage * itemsPerPage, data?.total || 0)} of{" "}
            {data?.total || 0}
          </Text>
          <Button
            size="xs"
            width="24px"
            variant="outline"
            paddingX={0}
            marginRight={2}
            onClick={handlePrevPage}
            disabled={currentPage === 1}
          >
            <PrevArrow />
          </Button>
          <Button
            size="xs"
            variant="outline"
            paddingX={0}
            onClick={handleNextPage}
            disabled={currentPage === totalPages || totalPages === 0}
          >
            <NextArrow />
          </Button>
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
