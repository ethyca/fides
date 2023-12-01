import { BASE_URL } from "~/constants";

type DateRange = {
  startDate?: string;
  endDate?: string;
};

export function convertDateRangeToSearchParams({
  startDate,
  endDate,
}: DateRange) {
  let startDateISO;
  if (startDate) {
    startDateISO = new Date(startDate);
    startDateISO.setUTCHours(0, 0, 0);
  }

  let endDateISO;
  if (endDate) {
    endDateISO = new Date(endDate);
    endDateISO.setUTCHours(0, 0, 0);
  }

  return {
    ...(startDateISO ? { created_gt: startDateISO.toISOString() } : {}),
    ...(endDateISO ? { created_lt: endDateISO.toISOString() } : {}),
  };
}

export const requestCSVDownload = async ({
  startDate,
  endDate,
  token,
}: DateRange & { token: string | null }) => {
  if (!token) {
    return null;
  }

  return fetch(
    `${BASE_URL}/consent-reporting?${new URLSearchParams({
      // TODO: figure out correct URL
      ...convertDateRangeToSearchParams({ startDate, endDate }),
      download_csv: "true",
    })}`,
    {
      headers: {
        "Access-Control-Allow-Origin": "*",
        Authorization: `Bearer ${token}`,
        "X-Fides-Source": "fidesops-admin-ui",
      },
    }
  )
    .then((response) => {
      if (!response.ok) {
        throw new Error("Got a bad response from the server");
      }
      return response.blob();
    })
    .then((data) => {
      const a = document.createElement("a");
      a.href = window.URL.createObjectURL(data);
      a.download = "consent-reports.csv";
      a.click();
    })
    .catch((error) => Promise.reject(error));
};
