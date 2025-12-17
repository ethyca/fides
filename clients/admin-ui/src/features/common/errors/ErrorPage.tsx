import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton,
  AntButtonProps,
  AntFlex,
  AntResult,
  AntTypography,
} from "fidesui";
import { ReactNode } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import ErrorImage from "~/features/common/errors/ErrorImage";
import { getErrorMessage } from "~/features/common/helpers";

type ActionProps = AntButtonProps & { label: ReactNode };

const ErrorPage = ({
  error,
  actions,
}: {
  error: FetchBaseQueryError | SerializedError;
  actions: ActionProps[];
}) => {
  const errorMessage = getErrorMessage(error);
  // handle both FetchBaseQueryError and SerializedError
  const dataString =
    "data" in error ? JSON.stringify(error.data) : JSON.stringify(error);
  const status = "status" in error ? error.status : undefined;

  return (
    <AntFlex vertical align="center" justify="center" className="h-screen">
      <AntResult
        status="error"
        icon={<ErrorImage status={status} />}
        title={`Error ${status}`}
        subTitle={
          <>
            <AntTypography.Paragraph type="secondary">
              {errorMessage}
            </AntTypography.Paragraph>
            <AntTypography.Text type="secondary">
              {dataString}
            </AntTypography.Text>
            <ClipboardButton copyText={dataString} />
          </>
        }
        extra={
          actions.length > 0 ? (
            <AntFlex gap="small" justify="center">
              {actions.map((action, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <AntButton key={index} {...action}>
                  {action.label}
                </AntButton>
              ))}
            </AntFlex>
          ) : undefined
        }
      />
    </AntFlex>
  );
};

export default ErrorPage;
