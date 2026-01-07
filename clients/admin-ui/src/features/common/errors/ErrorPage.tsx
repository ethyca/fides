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
import { getErrorMessage } from "~/features/common/helpers";

type ActionProps = Omit<ButtonProps, "children"> & { label: ReactNode };

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
    <Flex vertical align="center" justify="center" className="h-screen">
      <Result
        status="error"
        icon={<ErrorImage status={status} />}
        title={`Error ${status}`}
        data-testid="error-page-result"
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
