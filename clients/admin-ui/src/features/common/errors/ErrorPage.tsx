import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { AntButton, AntButtonProps, AntFlex, AntTypography } from "fidesui";

import ErrorImage from "~/features/common/errors/ErrorImage";
import { getErrorMessage } from "~/features/common/helpers";

const ErrorPage = ({
  error,
  actions,
}: {
  error: FetchBaseQueryError;
  actions: AntButtonProps[];
}) => {
  const { status, data } = error;
  // TODO: examine this error handling more carefully to extract the right message
  const errorMessage = getErrorMessage(error);
  return (
    <AntFlex vertical align="center" justify="center" className="h-screen">
      <AntFlex vertical gap="large" align="center">
        <ErrorImage status={status} />
        <AntTypography.Title level={1}>
          {status ? `Error ${status}` : "Unknown Error"}
        </AntTypography.Title>
        <AntTypography.Text>{errorMessage}</AntTypography.Text>
        {actions.length > 0 && (
          <AntFlex gap="small" justify="center">
            {actions.map((action, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <AntButton key={index} {...action} />
            ))}
          </AntFlex>
        )}
      </AntFlex>
    </AntFlex>
  );
};

export default ErrorPage;
