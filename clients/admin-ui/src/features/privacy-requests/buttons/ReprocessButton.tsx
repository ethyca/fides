import {
  Button,
  ButtonProps,
  forwardRef,
  ListItem,
  UnorderedList,
} from "@fidesui/react";
import { useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import { useAlert, useAPIHelper } from "../../common/hooks";
import {
  selectRetryRequests,
  setRetryRequests,
  useBulkRetryMutation,
  useRetryMutation,
} from "../privacy-requests.slice";
import { PrivacyRequest } from "../types";

type ReprocessButtonProps = {
  buttonProps?: ButtonProps;
  subjectRequest?: PrivacyRequest;
};

const ReprocessButton = forwardRef(
  ({ buttonProps, subjectRequest }: ReprocessButtonProps, ref) => {
    const dispatch = useAppDispatch();
    const [isReprocessing, setIsReprocessing] = useState(false);
    const { handleError } = useAPIHelper();
    const { errorAlert, successAlert } = useAlert();

    const { errorRequests } = useAppSelector(selectRetryRequests);
    const [bulkRetry] = useBulkRetryMutation();
    const [retry] = useRetryMutation();

    const handleBulkReprocessClick = () => {
      setIsReprocessing(true);
      bulkRetry(errorRequests!)
        .unwrap()
        .then((response) => {
          if (response.failed.length > 0) {
            errorAlert(
              <UnorderedList fontSize="sm" mt="8px">
                {response.failed.map((f, index) => (
                  <ListItem
                    key={f.data.privacy_request_id}
                    mt={index === 0 ? 0 : "8px"}
                  >
                    <b>Request Id:</b> {f.data.privacy_request_id}
                    <br />
                    <b>Message:</b> {f.message}
                  </ListItem>
                ))}
              </UnorderedList>,
              undefined,
              `DSR automation has failed for the following request(s):`,
              null,
              {
                maxWidth: "max-content",
              }
            );
          }
          if (response.succeeded.length > 0) {
            successAlert(`Data subject request(s) are now being reprocessed.`);
          }
        })
        .catch((error) => {
          dispatch(setRetryRequests({ checkAll: false, errorRequests: [] }));
          errorAlert(
            error,
            undefined,
            `DSR batch automation has failed due to the following:`
          );
        })
        .finally(() => {
          setIsReprocessing(false);
        });
    };

    const handleSingleReprocessClick = () => {
      setIsReprocessing(true);
      retry(subjectRequest!)
        .unwrap()
        .then(() => {
          successAlert(`Data subject request is now being reprocessed.`);
        })
        .catch((error) => {
          handleError(error);
        })
        .finally(() => {
          setIsReprocessing(false);
        });
    };

    return (
      <Button
        {...buttonProps}
        isDisabled={isReprocessing}
        isLoading={isReprocessing}
        loadingText="Reprocessing"
        onClick={
          subjectRequest ? handleSingleReprocessClick : handleBulkReprocessClick
        }
        ref={ref}
        spinnerPlacement="end"
        variant="outline"
        _hover={{
          bg: "gray.100",
        }}
        _loading={{
          opacity: 1,
          div: { opacity: 0.4 },
        }}
      >
        Reprocess
      </Button>
    );
  }
);

export default ReprocessButton;
