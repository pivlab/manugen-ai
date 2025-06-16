import { api, request } from "./";

import type { ADKResponse } from "./adk";

type Response = { output: string };

/** capitalizes the selected text using the capitalizer */
export const capitalizer = (input: string) =>
  request<ADKResponse>(`${api}/adk_api/run`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      "appName": "capitalizer",
      "userId": "falquaddoomi",
      "sessionId": "session-1749846534881",
      "newMessage": {
        "role": "user",
        "parts": [{
          "text": `Capitalize every word in this text: "${input}"`
        }]
      }
    }),
  });

/** arbitrary endpoint */
export const endpoint1 = (input: string) =>
  request<Response>(`${api}/endpoint1`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });

/** arbitrary endpoint */
export const endpoint2 = (input: string) =>
  request<Response>(`${api}/endpoint2`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });

/** arbitrary endpoint */
export const endpoint3 = (input: string) =>
  request<Response>(`${api}/endpoint3`, {
    method: "POST",
    body: JSON.stringify({ input }),
  });
