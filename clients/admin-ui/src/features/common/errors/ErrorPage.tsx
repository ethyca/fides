import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton,
  AntButtonProps,
  AntFlex,
  AntTooltip,
  AntTypography,
  Icons,
} from "fidesui";
import { ReactNode } from "react";

import ErrorImage from "~/features/common/errors/ErrorImage";
import { getErrorMessage } from "~/features/common/helpers";
import useClipboardButton from "~/features/common/hooks/useClipboard";

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
  const { tooltipText, handleCopy } = useClipboardButton(dataString);

  return (
    <AntFlex vertical align="center" justify="center" className="h-screen">
      <AntFlex vertical gap="middle" align="center">
        <ErrorImage status={status} />
        <AntTypography.Title level={1}>
          {status ? `Error ${status}` : "Unknown Error"}
        </AntTypography.Title>
        <AntTypography.Paragraph type="secondary">
          {errorMessage}
        </AntTypography.Paragraph>
        <AntFlex gap="small" align="center">
          <AntTypography.Text type="secondary">{dataString}</AntTypography.Text>
          <AntTooltip title={tooltipText} placement="top">
            <AntButton
              icon={<Icons.Copy />}
              aria-label="Copy error data"
              type="text"
              size="small"
              onClick={handleCopy}
            />
          </AntTooltip>
        </AntFlex>
        {actions.length > 0 && (
          <AntFlex gap="middle" justify="center">
            {actions.map((action, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <AntButton key={index} {...action}>
                {action.label}
              </AntButton>
            ))}
          </AntFlex>
        )}
      </AntFlex>
    </AntFlex>
  );
};

export default ErrorPage;
