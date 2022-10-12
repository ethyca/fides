import { Button, ButtonProps } from "@fidesui/react";
import React, { useState } from "react";

import { useAlert, useAPIHelper } from "../common/hooks";
import { useRetryMutation } from "./privacy-requests.slice";
import { PrivacyRequest } from "./types";

type ReprocessButtonProps = {
  buttonProps?: ButtonProps;
  ref?: React.LegacyRef<HTMLButtonElement>;
  subjectRequest: PrivacyRequest;
};

const ReprocessButton: React.FC<ReprocessButtonProps> = ({
  buttonProps,
  ref,
  subjectRequest,
}) => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [retry] = useRetryMutation();
  const [isReprocessing, setIsReprocessing] = useState(false);

  const handleReprocessClick = () => {
    setIsReprocessing(true);
    retry(subjectRequest)
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
      isLoading={isReprocessing}
      loadingText="Reprocessing"
      onClick={handleReprocessClick}
      ref={ref}
      size="xs"
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
};

export default ReprocessButton;
