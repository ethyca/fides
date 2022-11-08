import { useRouter } from "next/router";
import { useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features.slice";
import { resolveLink } from "~/features/common/nav/zone-config";

import { selectAddSystemsMethod } from "./config-wizard.slice";
import RegisterSystems from "./RegisterSystems";
import SystemsClassifyTable from "./SystemsClassifyTable";
import { SystemMethods } from "./types";

const ScanResults = () => {
  const method = useAppSelector(selectAddSystemsMethod);

  const router = useRouter();
  const features = useFeatures();

  const [isClassifying, setIsClassifying] = useState(false);

  const handleFinish = () => {
    const datamapRoute = resolveLink({
      href: "/datamap",
      basePath: "/",
    });

    return features.plus
      ? router.push(datamapRoute.href)
      : router.push("/system");
  };

  const handleStartClassify = () => {
    setIsClassifying(true);
  };

  if (isClassifying) {
    return <SystemsClassifyTable onFinish={handleFinish} />;
  }

  return (
    <RegisterSystems
      // Eventually, all scanners will go through some sort of classify flow.
      //  But for now, only the runtime scanner does
      onFinish={
        method === SystemMethods.RUNTIME ? handleStartClassify : handleFinish
      }
    />
  );
};

export default ScanResults;
