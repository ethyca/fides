import { AntButton } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import { STEPS } from "./constants";

const AddConnectionButton = () => {
  const router = useRouter();
  return (
    <AntButton onClick={() => router.push(STEPS[1].href)} type="primary">
      Create new connection
    </AntButton>
  );
};

export default AddConnectionButton;
