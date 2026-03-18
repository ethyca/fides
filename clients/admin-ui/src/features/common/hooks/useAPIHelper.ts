import { isErrorWithDetail, isErrorWithDetailArray } from "common/helpers";
import { useMessage } from "fidesui";

/**
 * Custom hook for API helper methods
 */
export const useAPIHelper = () => {
  const message = useMessage();

  /**
   * Display custom error toast notification as a result of an API exception
   */
  const handleError = (error: any) => {
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = error.data.detail[0].msg;
    }
    message.error(errorMsg);
  };

  return { handleError };
};
