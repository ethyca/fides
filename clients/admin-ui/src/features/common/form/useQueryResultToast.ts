import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import { RTKResult } from "~/types/errors";

const useQueryResultToast = ({
  defaultSuccessMsg,
  defaultErrorMsg,
}: {
  defaultSuccessMsg: string;
  defaultErrorMsg: string;
}) => {
  const { successAlert, errorAlert } = useAlert();
  const toastResult = (result: RTKResult) => {
    if (isErrorResult(result)) {
      const errorMsg = getErrorMessage(result.error, defaultErrorMsg);
      errorAlert(errorMsg);
    } else {
      successAlert(defaultSuccessMsg);
    }
  };

  return { toastResult };
};

export default useQueryResultToast;
