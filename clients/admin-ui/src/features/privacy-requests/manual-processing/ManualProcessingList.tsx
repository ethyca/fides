import {
  Box,
  Button,
  Center,
  Divider,
  Heading,
  Spinner,
  Table,
  TableContainer,
  Tbody,
  Td,
  Text,
  Tfoot,
  Th,
  Thead,
  Tr,
  VStack,
} from "@fidesui/react";
import { useAlert, useAPIHelper } from "common/hooks";
import { useGetAllEnabledAccessManualHooksQuery } from "datastore-connections/datastore-connection.slice";
import { useRouter } from "next/router";
import {
  privacyRequestApi,
  useResumePrivacyRequestFromRequiresInputMutation,
  useUploadManualWebhookDataMutation,
} from "privacy-requests/privacy-requests.slice";
import {
  PatchUploadManualWebhookDataRequest,
  PrivacyRequestEntity,
} from "privacy-requests/types";
import React, { useEffect, useState } from "react";
import { INDEX_ROUTE } from "src/constants";

import { useAppDispatch } from "~/app/hooks";

import ManualProcessingDetail from "./ManualProcessingDetail";
import { ManualInputData } from "./types";

type ManualProcessingListProps = {
  subjectRequest: PrivacyRequestEntity;
};

const ManualProcessingList: React.FC<ManualProcessingListProps> = ({
  subjectRequest,
}) => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [dataList, setDataList] = useState([] as unknown as ManualInputData[]);
  const [isCompleteDSRLoading, setIsCompleteDSRLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { data, isFetching, isLoading, isSuccess } =
    useGetAllEnabledAccessManualHooksQuery();

  const [resumePrivacyRequestFromRequiresInput] =
    useResumePrivacyRequestFromRequiresInputMutation();

  const [uploadManualWebhookData] = useUploadManualWebhookDataMutation();

  const handleCompleteDSRClick = async () => {
    try {
      setIsCompleteDSRLoading(true);
      await resumePrivacyRequestFromRequiresInput(subjectRequest.id).unwrap();
      successAlert(`Manual request has been received. Request now processing.`);
      router.push(INDEX_ROUTE);
    } catch (error) {
      handleError(error);
    } finally {
      setIsCompleteDSRLoading(false);
    }
  };

  const handleSubmit = async (params: PatchUploadManualWebhookDataRequest) => {
    try {
      setIsSubmitting(true);
      await uploadManualWebhookData(params).unwrap();
      const response = {
        connection_key: params.connection_key,
        fields: {},
      };
      Object.entries(params.body).forEach(([key, value]) => {
        // @ts-ignore
        response.fields[key] = value || "";
      });
      // Update the manual input data state
      const newState = dataList.map((item) => {
        if (item.connection_key === response.connection_key) {
          return { ...item, checked: true, fields: { ...response.fields } };
        }
        return item;
      });
      setDataList(newState);
      successAlert(`Manual input successfully saved!`);
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    const fetchUploadedManuaWebhookData = () => {
      if (dataList.length > 0) {
        return;
      }
      const promises: any[] = [];
      const keys = data?.map((item) => item.connection_config.key);
      keys?.every((k) =>
        promises.push(
          dispatch(
            privacyRequestApi.endpoints.getUploadedManualWebhookData.initiate({
              connection_key: k,
              privacy_request_id: subjectRequest.id,
            })
          )
        )
      );
      Promise.allSettled(promises).then((results) => {
        const list: ManualInputData[] = [];
        results.forEach((result, index) => {
          if (
            result.status === "fulfilled" &&
            result.value.isSuccess &&
            result.value.data
          ) {
            const item = {
              checked: result.value.data.checked,
              fields: {},
              connection_key: result.value.originalArgs.connection_key,
              privacy_request_id: result.value.originalArgs.privacy_request_id,
            } as ManualInputData;
            Object.entries(result.value.data.fields).forEach(([key, value]) => {
              // @ts-ignore
              item.fields[key] = value || "";
            });
            list.push(item);
          } else {
            errorAlert(
              `An error occurred while loading manual input data for ${
                data![index].connection_config.name
              }`
            );
          }
        });
        setDataList(list);
      });
    };

    if (isSuccess && data!.length > 0 && dataList.length === 0) {
      fetchUploadedManuaWebhookData();
    }

    return () => {};
  }, [
    data,
    dataList.length,
    dispatch,
    errorAlert,
    isSuccess,
    subjectRequest.id,
  ]);

  return (
    <VStack align="stretch" spacing={8}>
      <Box>
        <Heading color="gray.900" fontSize="lg" fontWeight="semibold" mb={4}>
          Manual Processing
        </Heading>
        <Divider />
      </Box>
      <Box>
        <Text color="gray.700" fontSize="sm">
          The following table details the integrations that require manual input
          from you.
        </Text>
      </Box>
      <Box>
        {(isFetching || isLoading) && (
          <Center>
            <Spinner />
          </Center>
        )}
        {isSuccess && data ? (
          <TableContainer>
            <Table size="sm" variant="unstyled">
              <Thead>
                <Tr>
                  <Th
                    fontSize="sm"
                    fontWeight="semibold"
                    pl="0"
                    textTransform="none"
                  >
                    Connector name
                  </Th>
                  <Th fontSize="sm" fontWeight="semibold" textTransform="none">
                    Description
                  </Th>
                  <Th />
                </Tr>
              </Thead>
              <Tbody>
                {data.length > 0 &&
                  data.map((item) => (
                    <Tr key={item.id}>
                      <Td pl="0">{item.connection_config.name}</Td>
                      <Td>{item.connection_config.description}</Td>
                      <Td>
                        {dataList.length > 0 ? (
                          <ManualProcessingDetail
                            connectorName={item.connection_config.name}
                            data={
                              dataList.find(
                                (i) =>
                                  i.connection_key ===
                                  item.connection_config.key
                              ) as ManualInputData
                            }
                            isSubmitting={isSubmitting}
                            onSaveClick={handleSubmit}
                          />
                        ) : null}
                      </Td>
                    </Tr>
                  ))}
                {data.length === 0 && (
                  <Tr>
                    <Td colSpan={3} pl="0">
                      <Center>
                        <Text>
                          You don&lsquo;t have any Manual Process connections
                          set up yet.
                        </Text>
                      </Center>
                    </Td>
                  </Tr>
                )}
              </Tbody>
              {dataList.length > 0 && dataList.every((item) => item.checked) ? (
                <Tfoot>
                  <Tr>
                    <Th />
                    <Th />
                    <Th>
                      <Button
                        color="white"
                        bg="primary.800"
                        fontSize="xs"
                        h="24px"
                        isLoading={isCompleteDSRLoading}
                        loadingText="Completing DSR"
                        onClick={handleCompleteDSRClick}
                        w="127px"
                        _hover={{ bg: "primary.400" }}
                        _active={{ bg: "primary.500" }}
                      >
                        Complete DSR
                      </Button>
                    </Th>
                  </Tr>
                </Tfoot>
              ) : null}
            </Table>
          </TableContainer>
        ) : null}
      </Box>
    </VStack>
  );
};

export default ManualProcessingList;
