import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { Image } from "fidesui";

const ERROR_IMAGE_PATH = "/images/errors";

const ErrorImage = ({ status }: { status?: FetchBaseQueryError["status"] }) => {
  if (status === 404) {
    return (
      <Image
        src={`${ERROR_IMAGE_PATH}/404.svg`}
        alt="Error 404"
        preview={false}
      />
    );
  }
  if (status === 500) {
    return (
      <Image
        src={`${ERROR_IMAGE_PATH}/500.svg`}
        alt="Error 500"
        preview={false}
      />
    );
  }
  return (
    <Image
      src={`${ERROR_IMAGE_PATH}/unknown.svg`}
      alt="Error Unknown"
      preview={false}
    />
  );
};

export default ErrorImage;
