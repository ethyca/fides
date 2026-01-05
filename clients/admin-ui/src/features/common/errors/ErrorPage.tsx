import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton,
  AntButtonProps,
  AntCollapse,
  AntFlex,
  AntResult,
  AntTypography,
} from "fidesui";
import { useRouter } from "next/router";
import { ReactNode } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import ErrorImage from "~/features/common/errors/ErrorImage";
import { getErrorMessage } from "~/features/common/helpers";

type ActionProps = Omit<AntButtonProps, "children"> & { label: ReactNode };

const ErrorPage = ({
  error,
  defaultMessage = "An unexpected error occurred.  Please try again",
  actions,
  showReload = true,
}: {
  error: FetchBaseQueryError | SerializedError;
  defaultMessage?: string;
  actions?: ActionProps[];
  showReload?: boolean;
}) => {
  const errorMessage = getErrorMessage(error, defaultMessage);
  // handle both FetchBaseQueryError and SerializedError
  const dataString =
    "data" in error ? JSON.stringify(error.data) : JSON.stringify(error);
  const status = "status" in error ? error.status : undefined;

  const router = useRouter();

  const showActions = (actions && actions.length > 0) || showReload;

  return (
    <AntFlex vertical align="center" justify="center" className="h-screen">
      <AntResult
        status="error"
        icon={<ErrorImage status={status} />}
        title={`Error ${status}`}
        data-testid="error-page-result"
        subTitle={
          <>
            <AntTypography.Paragraph type="secondary">
              {errorMessage}
            </AntTypography.Paragraph>
            <AntFlex justify="start" className="max-w-96">
              <AntCollapse
                ghost
                size="small"
                items={[
                  {
                    key: "1",
                    label: "Show details",
                    classNames: {
                      header: "w-fit",
                    },
                    children: (
                      <>
                        <AntTypography.Text type="secondary">
                          {dataString}
                        </AntTypography.Text>
                        <ClipboardButton copyText={dataString} />
                      </>
                    ),
                  },
                ]}
              />
            </AntFlex>
          </>
        }
        extra={
          showActions && (
            <AntFlex gap="small" justify="center">
              {actions?.map((action, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <AntButton key={index} {...action}>
                  {action.label}
                </AntButton>
              ))}
              {showReload && (
                <AntButton onClick={() => router.reload()} type="primary">
                  Reload
                </AntButton>
              )}
            </AntFlex>
          )
        }
      />
    </AntFlex>
  );
};

export default ErrorPage;
