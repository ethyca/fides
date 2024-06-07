import { useToast } from "fidesui";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { RTKResult } from "~/types/errors";

const useQueryResultToast = ({
  defaultSuccessMsg,
  defaultErrorMsg,
}: {
  defaultSuccessMsg: string;
  defaultErrorMsg: string;
}) => {
  const toast = useToast();
  const toastResult = (result: RTKResult) => {
    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(result.error, defaultErrorMsg);
      toast({ status: "error", description: errorMsg });
    } else {
      toast({ status: "success", description: defaultSuccessMsg });
    }
  };

  return { toastResult };
};

export default useQueryResultToast;
