import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { Button, ButtonProps, Flex, Result, Typography } from "fidesui";
import { ReactNode } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";
import ErrorImage from "~/features/common/errors/ErrorImage";
import { getErrorMessage } from "~/features/common/helpers";

type ActionProps = ButtonProps & { label: ReactNode };

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
    <Flex vertical align="center" justify="center" className="h-screen">
      <Result
        status="error"
        icon={<ErrorImage status={status} />}
        title={`Error ${status}`}
        subTitle={
          <>
            <Typography.Paragraph type="secondary">
              {errorMessage}
            </Typography.Paragraph>
            <Typography.Text type="secondary">{dataString}</Typography.Text>
            <ClipboardButton copyText={dataString} />
          </>
        }
        extra={
          actions.length > 0 ? (
            <Flex gap="small" justify="center">
              {actions.map((action, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <Button key={index} {...action}>
                  {action.label}
                </Button>
              ))}
            </Flex>
          ) : undefined
        }
      />
    </Flex>
  );
};

export default ErrorPage;
