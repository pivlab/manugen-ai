import { toast, type ToastOptions } from 'vue3-toastify';

import { api, request } from "./";

import {
  ensureSessionExists, extractADKText, sseRequest,
  type ADKResponse, type ADKResponsePart, type ADKSessionResponse
} from "./adk";

type Response = { output: string };

/** capitalizes the selected text using the capitalizer */
export const capitalizer = async (input: string, session: ADKSessionResponse) => {
  return request<ADKResponse>(`${api}/adk_api/run`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      "appName": session.appName,
      "userId": session.userId,
      "sessionId": session.id,
      "newMessage": {
        "role": "user",
        "parts": [{
          "text": `Capitalize every word in this text: "${input}". Include only the text, no additional information.`,
        }]
      }
    }),
  });
}

/** dispatches to ai_science_writer for a variety of actions */
export const aiWriter = async (input: string, session: ADKSessionResponse|null) => {
  if (!session) {
    console.error("No session provided for aiWriter, aborting");
    return
  }
  if (session.appName !== "ai_science_writer") {
    console.error("Session appName is not 'ai_science_writer', aborting");
    return
  }

  return request<ADKResponse>(`${api}/adk_api/run`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      "appName": session.appName,
      "userId": session.userId,
      "sessionId": session.id,
      "newMessage": {
        "role": "user",
        "parts": [{
          "text": input,
        }]
      }
    }),
  });
}

export const aiWriterAsync = async (input: string, session: ADKSessionResponse|null) => {
  if (!session) {
    console.error("No session provided for aiWriter, aborting");
    return
  }
  else if (session.appName !== "ai_science_writer") {
    console.error("Session appName is not 'ai_science_writer', aborting");
    return
  }

  // immediately returns an EventSource-like object
  const eventLog: ADKResponse = await sseRequest(`${api}/adk_api/run_sse`, {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
    },
    payload: JSON.stringify({
      "appName": session.appName,
      "userId": session.userId,
      "sessionId": session.id,
      "newMessage": {
        "role": "user",
        "parts": [{
          "text": input,
        }]
      }
    }),
  }, (event: ADKResponsePart) => {
    console.log("Received event:", event);

    let msg = null; // `Action by ${event?.author}`;

    if (event) {
      // inspect the event to see how to format it
      if (event.actions?.transferToAgent) {
        msg = `<b>${event.author}</b> =><br /> ${event.actions.transferToAgent}`
      }
      else if (event.content?.parts[0]?.text) {
        msg = `<b>${event.author}</b><br />produced text`
      }

      if (msg) {
        toast(msg, {
          position: "bottom-left",
          autoClose: 6000,
          hideProgressBar: true,
          type: "info",
          transition: "bounce",
        } as ToastOptions);
      }
    }
  });

  console.log("Final event log received:", eventLog);

  return eventLog;
}
