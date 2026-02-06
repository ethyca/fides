import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Button,
  ButtonProps,
  Collapse,
  Flex,
  Result,
  Typography,
} from "fidesui";
import { useRouter } from "next/router";
import { ReactNode } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import ErrorImage from "~/features/common/errors/ErrorImage";
import { getErrorMessage, ParsedError } from "~/features/common/helpers";

type ActionProps = Omit<ButtonProps, "children"> & { label: ReactNode };

type ErrorPageError = FetchBaseQueryError | SerializedError | ParsedError;

const isParsedError = (error: ErrorPageError): error is ParsedError =>
  "message" in error &&
  "status" in error &&
  typeof error.message === "string" &&
  typeof error.status === "number" &&
  !("data" in error);

const DEFAULT_MESSAGE = "An unexpected error occurred.  Please try again";

const ErrorPage = ({
  error,
  defaultMessage,
  actions,
  showReload = true,
  fullScreen = true,
}: {
  error: ErrorPageError;
  defaultMessage?: string;
  actions?: ActionProps[];
  showReload?: boolean;
  fullScreen?: boolean;
}) => {
  const errorMessage = isParsedError(error)
    ? (defaultMessage ?? error.message)
    : getErrorMessage(error, defaultMessage ?? DEFAULT_MESSAGE);
  // handle FetchBaseQueryError, SerializedError, and ParsedError
  const getDataString = () => {
    if (isParsedError(error)) {
      return error.message;
    }
    if ("data" in error && !!error.data) {
      return JSON.stringify(error.data);
    }
    return JSON.stringify(error);
  };
  const dataString = getDataString();
  const status = "status" in error && !!error.status ? error.status : undefined;

  const router = useRouter();

  const showActions = (actions && actions.length > 0) || showReload;

  return (
    <Flex
      vertical
      align="center"
      justify="center"
      className={fullScreen ? "h-screen" : ""}
      data-testid="error-page-result"
    >
      <Result
        status="error"
        icon={<ErrorImage status={status} />}
        title={`Error ${status}`}
        subTitle={
          <>
            <Typography.Paragraph type="secondary">
              {errorMessage}
            </Typography.Paragraph>
            <Flex justify="start" className="max-w-96">
              <Collapse
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
                        <Typography.Text type="secondary">
                          {dataString}
                        </Typography.Text>
                        <ClipboardButton copyText={dataString} />
                      </>
                    ),
                  },
                ]}
              />
            </Flex>
          </>
        }
        extra={
          showActions && (
            <Flex gap="small" justify="center">
              {actions?.map((action, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <Button key={index} {...action}>
                  {action.label}
                </Button>
              ))}
              {showReload && (
                <Button onClick={() => router.reload()} type="primary">
                  Reload
                </Button>
              )}
            </Flex>
          )
        }
      />
    </Flex>
  );
};

export default ErrorPage;
