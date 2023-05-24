import { isErrorWithDetail, isErrorWithDetailArray } from "common/helpers";

import { useAlert } from "./useAlert";

/**
 * Custom hook for API helper methods
 * @returns
 */
export const useAPIHelper = () => {
  const { errorAlert } = useAlert();

  /**
   * Display custom error toast notification as a result of an API exception
   * @param error
   */
  const handleError = (error: any) => {
    console.log(error);
    let errorMsg = "An unexpected error occurred. Please try again.";
    if (isErrorWithDetail(error)) {
      errorMsg = error.data.detail;
    } else if (isErrorWithDetailArray(error)) {
      errorMsg = error.data.detail[0].msg;
    }
    errorAlert(errorMsg);
  };

  return { handleError };
};
