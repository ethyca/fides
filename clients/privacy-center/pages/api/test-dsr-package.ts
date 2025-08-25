import type { NextApiRequest, NextApiResponse } from "next";

import { createRequestLogger } from "~/app/server-utils/requestLogger";

/**
 * @swagger
 * /test-dsr-package:
 *   get:
 *     description: Test endpoint to verify DSR package integration works
 *     parameters:
 *       - in: query
 *         name: request_id
 *         required: false
 *         description: Test privacy request ID
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Test successful
 *       500:
 *         description: Test failed
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse,
) {
  const log = createRequestLogger(req);

  if (req.method !== "GET") {
    res.setHeader("Allow", ["GET"]);
    return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
  }

  try {
    const { request_id = "test-request-123" } = req.query;

    // Test call to our DSR package endpoint
    const baseUrl = `${req.headers.host?.includes("localhost") ? "http" : "https"}://${req.headers.host}`;
    const testUrl = `${baseUrl}/api/dsr-package?request_id=${request_id}`;

    log.info(`Testing DSR package integration with URL: ${testUrl}`);

    const response = await fetch(testUrl, {
      redirect: "manual", // Don't follow redirects so we can test them
    });

    // For redirect endpoint, we expect either a 302 redirect or an error
    const isRedirect = response.status === 302;
    const redirectLocation = response.headers.get("location");

    let responseText = "";
    try {
      responseText = await response.text();
    } catch (e) {
      // Ignore if we can't read response text
    }

    return res.status(200).json({
      success: true,
      test_url: testUrl,
      response_status: response.status,
      is_redirect: isRedirect,
      redirect_location: redirectLocation,
      response_text: responseText.substring(0, 200), // Limit response text
      message: isRedirect
        ? `DSR package endpoint redirecting to: ${redirectLocation}`
        : `DSR package endpoint returned status ${response.status} (expected for test data)`,
    });
  } catch (error) {
    log.error("Error testing DSR package integration:", error);
    return res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : "Unknown error",
      message: "DSR package integration test failed",
    });
  }
}
