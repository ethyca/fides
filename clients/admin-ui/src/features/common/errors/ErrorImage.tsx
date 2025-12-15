import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { AntImage } from "fidesui";

const ERROR_IMAGE_PATH = "/images/errors";

const ErrorImage = ({ status }: { status: FetchBaseQueryError["status"] }) => {
  if (status === 404) {
    return (
      <AntImage
        src={`${ERROR_IMAGE_PATH}/404.png`}
        alt="Error 404"
        preview={false}
      />
    );
  }
  if (status === 500) {
    return (
      <AntImage
        src={`${ERROR_IMAGE_PATH}/500.png`}
        alt="Error 500"
        preview={false}
      />
    );
  }
  return (
    <AntImage
      src={`${ERROR_IMAGE_PATH}/unknown.png`}
      alt="Error Unknown"
      preview={false}
    />
  );
};

export default ErrorImage;
