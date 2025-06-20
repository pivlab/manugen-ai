/*
contains ADK-specific types, api wrappers, and utility functions
*/

import { SSE } from "sse.js"
import { api, request } from "./"
import { waitForEventSourceToClose } from "@/util/events.ts"


// ============================================================================
// === Sessions
// ============================================================================

export type ADKSessionResponse = {
    "id": string,
    "appName": string,
    "userId": string,
    [key: string]: any
}

/**
 *  ensures that a session exists for the current user
 */
export const ensureSessionExists = async (appName: string, userId: string, sessionId : string|null) => {
  // perform GET for the session
  try {
    const result = await fetch(`${api}/adk_api/apps/${appName}/users/${userId}/sessions/${sessionId}`)
    // check that result is not 200 OK
    // this will immediately be caught below to attempt to create a new session
    if (!result.ok) {
      throw new Error(`Session for app ${appName} and user ${userId} does not exist`);
    }
    // if it is 200 OK, return the session
    return await result.json() as ADKSessionResponse;
  }
  catch (e) {
    // if it fails, create a new session
    const createResponse = await fetch(`${api}/adk_api/apps/${appName}/users/${userId}/sessions/${sessionId}`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        "state": {}
      }),
    });

    if (!createResponse.ok) {
      throw new Error(`Failed to create session for app ${appName} and user ${userId}`);
    }

    return await createResponse.json() as ADKSessionResponse;
  }
}

// ============================================================================
// === Content Uploads
// ============================================================================

export const uploadArtifact = async (session: ADKSessionResponse, filename: string, content: string, mimetype: string) => {
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
        "parts": [
          {
            "inlineData": {
              "displayName": filename,
              "data": content,
              "mimeType": mimetype
            }
          }
        ]
      }
    }),
  });
}


// ============================================================================
// === Response Modeling, Sending, Parsing
// ============================================================================

/*
ADK sends a response from /run or /run_sse back as a list of objects, where each
object represents a set of function invocations, function
responses, and text responses back to the user.
each response is of the following form:
{
  "content": {
    "parts": [{"<type>": <data>}],
    "role": "<role>>"
  },
  ...
}
<type> can  be "text", "functionCall", or "functionResponse"
- for the function types, the <data> payload is an object
  that contains, e.g., the arguments or the return value
- for the text type, the <data> payload is a string
<role> can be "user" or "model", and seems to vary depending on who's
  asking who (e.g. function responses come in with the role "user")
*/
export type ADKResponsePart = {
    "content": {
        "parts": {[key:string]: any}[],
        "role": string
    },
    "partial": boolean,
    "usageMetadata": {
        "candidatesTokenCount": bigint,
        "promptTokenCount": bigint,
        "totalTokenCount": bigint
    },
    "invocationId": string,
    "author": string,
    "actions": {
        "stateDelta": {
            [key:string]: string
        },
        "artifactDelta": object,
        "requestedAuthConfigs": object
    },
    "id": string,
    "timestamp": number
}
export type ADKResponse = ADKResponsePart[]

/**
 * Utility method to send an SSE request to the ADK API
 * @param url the URL to send the request to
 * @param options options to pass to the request, e.g. headers, method, body, etc.
 * @param msgCallback optional callback that will be called with the event log
 *                   as it is received. This is useful for streaming responses
 *                   and will be called with an array of ADKResponsePart objects
 *                   as they are received from the server.
 * @returns a promise that resolves to an array of ADKResponsePart objects
 *          representing the full response from the server.
 */
export const sseRequest = async (
  url: string,
  options: object = {},
  msgCallback?: (eventLog: ADKResponse) => void,
) => {
  /**
   * start request, listen for events and execute msgCallback if provided
   * blocks until the EventSource is closed or there's an error
   * see https://github.com/mpetazzoni/sse.js for details
   * */

  console.log("Posting to ADK API at", url, "with options", options);

  const source = new SSE(url, options);

  if (!source) {
    throw new Error("Failed to create SSE source");
  }

  const eventLog = [] as ADKResponse;

  // we append each event as we receive it
  source.addEventListener('message', (event: { data: string; }) => {
    const eventData = JSON.parse(event.data);
    eventLog.push(eventData)
    if (msgCallback) {
      msgCallback(eventLog);
    }
  })

  // block until the EventSource is closed
  await waitForEventSourceToClose(source);

  return eventLog;
}


/**
 * Utility method to extract 'text' sections from an ADK API response
 *
 * @param response - The ADK API response to extract text from
 * @param onlyLast - If true, returns only the last text section; if false,
 *                  returns all text sections concatenated with newlines
 * @returns The extracted text as a string
*/
export const extractADKText = (response: ADKResponse|undefined, onlyLast: boolean = true): string => {
  // if response is undefined, return an empty string
  if (!response) {
    return "";
  }

  const textSections = response
    .filter(item => item.content && item.content.parts)
    .map(item => item.content.parts)
    .map(parts => {
      // filter for parts that are of type "text"
      const textParts = parts.filter(part => part.text !== undefined);
      // if there are no text parts, return an empty string
      if (textParts.length === 0) return "";
      // otherwise, return the text of the first text part
      return textParts.map(x => x.text).join("\n");
  })

  if (onlyLast) {
    // if onlyLast is true, return the last text section
    return textSections.length > 0 ? textSections[textSections.length - 1] : "";
  }
  else {
    // if onlyLast is false, return all text sections concatenated
    return textSections.join("\n");
  }
}
