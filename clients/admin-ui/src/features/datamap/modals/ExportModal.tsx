import {
  Button,
  Divider,
  Flex,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Radio,
  RadioGroup,
  Stack,
  Text,
} from "@fidesui/react";
import { stringify } from "csv-stringify/sync";
import { saveAs } from "file-saver";
import React, {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { utils, WorkBook, writeFileXLSX } from "xlsx";

import { useAppSelector } from "~/app/hooks";
import QuestionTooltip from "~/features/common/QuestionTooltip";

import { EXPORT_FILTER_MAP, ExportFilterType } from "../constants";
import {
  DatamapColumn,
  DatamapRow,
  DatamapTableData,
  selectColumns,
  useLazyGetDatamapQuery,
} from "../datamap.slice";
import DatamapTableContext from "../datamap-table/DatamapTableContext";

export type ExportFileType = "xlsx" | "csv";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ isOpen, onClose }) => {
  const initialRef = useRef(null);
  const [selectedFilter, setSelectedFilter] = useState<number>(
    ExportFilterType.DEFAULT
  );
  const tableColumns = useAppSelector(selectColumns);
  const { tableInstance } = useContext(DatamapTableContext);
  const [getDatamap] = useLazyGetDatamapQuery();

  const applyMergeFilter = async (data: DatamapTableData) => {
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const _ = (await import("lodash")).default;
    const key = EXPORT_FILTER_MAP.find(
      (item) => item.id === selectedFilter
    )?.key;
    if (key) {
      const DELIMITER = ", ";
      return _.chain(data.rows)
        .groupBy((element) => element[key])
        .map((rows) => {
          let merge: DatamapRow = {};
          rows.forEach((r) => {
            merge = _.mergeWith(
              merge,
              r,
              (objValue: string, srcValue: string) => {
                if (typeof objValue === "string") {
                  if (objValue === srcValue || objValue.includes(srcValue)) {
                    return objValue;
                  }
                  const list = objValue.split(DELIMITER);
                  list.push(srcValue);
                  return list.sort().join(DELIMITER);
                }
                return srcValue;
              }
            );
          });
          return merge;
        })
        .sortBy(key)
        .value();
    }
    return data.rows;
  };

  const generateExportFile = (
    data: {
      columns: string[] | null;
      rows: string[][] | null;
    } | null,
    fileType: ExportFileType
  ) => {
    if (!data || !data.columns || !data.rows) {
      return "";
    }

    const { columns, rows } = data;

    // If we are generating a CSV file, do that and return
    if (fileType === "csv") {
      return stringify([columns, ...rows]);
    }

    // Generate XLSX worksheet
    const worksheet = utils.aoa_to_sheet([columns, ...rows]);
    const workbook = utils.book_new();
    utils.book_append_sheet(workbook, worksheet, "Datamap");

    return workbook;
  };

  const visibleColumns = useMemo(
    () => tableColumns?.filter((column) => column.isVisible) || [],
    [tableColumns]
  );

  const generateROPAExportData = async () => {
    const { data } = await getDatamap(
      {
        organizationName: "default_organization",
      },
      true
    );
    if (!data) {
      return null;
    }
    const columns = visibleColumns.map((column) => column.text);
    const mergeFilter = applyMergeFilter(data);
    const rows = (await mergeFilter).map((row) =>
      visibleColumns.reduce(
        (fields, column: DatamapColumn) => [...fields, `${row[column.value]}`],
        [] as string[]
      )
    );
    return { columns, rows };
  };

  const getFilterItem = useCallback(
    (id: ExportFilterType) => EXPORT_FILTER_MAP.find((item) => item.id === id),
    []
  );

  const handleChange = (nextValue: string) => {
    setSelectedFilter(Number(nextValue));
  };

  const isColumnVisible = useCallback(
    (key: string) =>
      key
        ? visibleColumns.some(
            (column) => column.value.toLowerCase() === key.toLowerCase()
          )
        : true,
    [visibleColumns]
  );

  const hasDisabledFilter = useMemo(
    () =>
      [
        ExportFilterType.GROUP_BY_PURPOSE_OF_PROCESSING,
        ExportFilterType.GROUP_BY_SYSTEM,
      ].some((value) => !isColumnVisible(getFilterItem(value)!.key)),
    [getFilterItem, isColumnVisible]
  );

  const triggerExportFileDownload = (
    file: string | WorkBook,
    fileType: ExportFileType
  ) => {
    const now = new Date().toISOString();
    const fileName = `${
      getFilterItem(selectedFilter)!.fileName
    }.${fileType}`.replace("[timestamp]", now);
    if (typeof file === "string") {
      if (fileType === "csv") {
        const blob = new Blob([file], { type: "text/csv;charset=utf-8" });
        saveAs(blob, fileName);
      }
    } else {
      writeFileXLSX(file, fileName);
    }
  };

  const handleExportClick = async (fileType: ExportFileType) => {
    onClose();
    if (!tableInstance) {
      return;
    }
    const data = await generateROPAExportData();
    const file = generateExportFile(data, fileType);
    triggerExportFileDownload(file, fileType);
  };

  useEffect(() => {
    if (isOpen) {
      setSelectedFilter(ExportFilterType.DEFAULT);
    }
  }, [isOpen]);

  return (
    <Modal
      initialFocusRef={initialRef}
      isCentered
      isOpen={isOpen}
      onClose={onClose}
      size="lg"
    >
      <ModalOverlay />
      <ModalContent minWidth="605px">
        <ModalHeader>
          <Flex flexDir="column" gap="16px">
            <Text>Export</Text>
            <Divider color="gray.200" />
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb="8px" pt="8px">
          <Flex
            alignItems="center"
            color="gray.700"
            gap="7.5px"
            fontSize="md"
            fontWeight="600"
            pb="16px"
          >
            Choose a format
            {hasDisabledFilter && (
              <QuestionTooltip
                hasArrow
                label="Some format options are unavailable. To access these options, ensure the system or purpose of processing columns are included in the report."
              />
            )}
          </Flex>
          <Flex justifyContent="space-between" mt="12px" width="100%">
            <RadioGroup
              colorScheme="secondary"
              onChange={handleChange}
              size="sm"
              value={selectedFilter}
            >
              <Stack direction="column" spacing="24px">
                {EXPORT_FILTER_MAP.map((item, index) => (
                  <Flex
                    alignItems="baseline"
                    cursor={
                      isColumnVisible(item.key) ? "pointer" : "not-allowed"
                    }
                    gap="12px"
                    key={item.key}
                    onClick={() => {
                      handleChange(item.id.toString());
                    }}
                  >
                    <Radio
                      isDisabled={!isColumnVisible(item.key)}
                      key={item.id}
                      ref={index === 2 ? initialRef : null}
                      spacing="12px"
                      value={item.id}
                      _disabled={{
                        background: "none",
                      }}
                    />
                    <Flex direction="column">
                      <Text
                        color={
                          isColumnVisible(item.key) ? "gray.700" : "gray.300"
                        }
                        fontSize="sm"
                        fontWeight="600"
                        lineHeight="20px"
                      >
                        {item.name}
                      </Text>
                      <Text color="gray.500" fontSize="xs" mt="6px">
                        {item.description}
                      </Text>
                    </Flex>
                  </Flex>
                ))}
              </Stack>
            </RadioGroup>
          </Flex>
        </ModalBody>
        <ModalFooter>
          <Flex
            borderTop="1px solid"
            borderTopColor="gray.200"
            justifyContent="space-between"
            pt="24px"
            width="100%"
          >
            <Button
              colorScheme="primary"
              size="sm"
              mr={3}
              flexGrow={1}
              onClick={() => handleExportClick("xlsx")}
            >
              Export Excel (.xls)
            </Button>
            <Button
              colorScheme="primary"
              size="sm"
              flexGrow={1}
              onClick={() => handleExportClick("csv")}
            >
              Export CSV (.csv)
            </Button>
          </Flex>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ExportModal;
