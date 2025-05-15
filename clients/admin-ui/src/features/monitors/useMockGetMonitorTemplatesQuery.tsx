import { useToast } from "fidesui";
import { useEffect, useState } from "react";

import { successToastParams } from "~/features/common/toast";
import {
  MonitorTemplateCreate,
  MonitorTemplateListResponse,
  MonitorTemplateResponse,
  MonitorTemplateUpdate,
} from "~/features/monitors/types";

const DUMMY_CONFIG_LIST: MonitorTemplateListResponse = {
  items: [
    {
      id: "config-1",
      name: "Test Config 1",
      regexCount: "20",
    },
    {
      id: "config-2",
      name: "Test Config 2",
      regexCount: "10",
    },
    {
      id: "config-3",
      name: "Test Config 3",
      regexCount: "5",
    },
  ],
  total: 3,
  pages: 1,
  page: 1,
  size: 10,
};

export const DUMMY_CONFIG_DETAIL: MonitorTemplateResponse = {
  id: "config-1",
  name: "Test config",
  regexMap: [
    ["test-regex-1", "test-data-category-1"],
    ["test-regex-2", "test-data-category-2"],
    ["test-regex-3", "test-data-category-3"],
  ],
};

export const useMockGetAllMonitorTemplatesQuery = () => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  }, []);

  return {
    data: DUMMY_CONFIG_LIST,
    isLoading,
  };
};

export const useMockGetMonitorTemplateByIdQuery = ({ id }: { id: string }) => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  }, []);

  return {
    data: DUMMY_CONFIG_DETAIL,
    isLoading,
  };
};

export const useMockCreateMonitorTemplateQuery = () => {
  const toast = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const trigger = (payload: MonitorTemplateCreate) => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    console.log("payload", payload);
    toast(successToastParams("Monitor template created successfully"));
  };

  return { trigger, isLoading };
};

export const useMockUpdateMonitorTemplateQuery = () => {
  const toast = useToast();
  const [isLoading, setIsLoading] = useState(false);

  const trigger = (payload: MonitorTemplateUpdate) => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    console.log("payload", payload);
    toast(successToastParams("Monitor template updated successfully"));
  };

  return { trigger, isLoading };
};
