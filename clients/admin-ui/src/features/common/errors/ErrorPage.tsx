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
  error: FetchBaseQueryError;
  actions: ActionProps[];
}) => {
  const { status, data } = error;
  // TODO: examine this error handling more carefully to extract the right message
  const errorMessage = getErrorMessage(error);
  const dataString = JSON.stringify(data);

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
