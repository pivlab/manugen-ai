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
export const ensureSessionExists = async (
  appName: string, userId: string, sessionId : string|null,
  maxRetries: number = 120, sleepBetweenRetriesMs: number = 1000
) => {
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
    let retries = maxRetries;

    while (retries >= 0) {
      try {
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
      catch (internalError) {
        // this can come either from the fetch failing due to the backend being down,
        // or from the response not being 200 OK
        // since we don't want to overwhelm the user with errors, we'll skip
        // reporting unless it's our last retry

        // console.error(`Error creating session for app ${appName} and user ${userId}:`, internalError);

        // if retries are exhausted, throw the error
        if (retries == 0) {
          throw internalError;
        }

        // otherwise, give it another shot in sleepBetweenRetriesMs milliseconds
        retries -= 1;
        // sleep for sleepBetweenRetries before retrying
        await new Promise(resolve => setTimeout(resolve, sleepBetweenRetriesMs));
        continue;
      }
    }
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
        "requestedAuthConfigs": object,
        "transferToAgent": string|undefined
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
  msgCallback?: (event: ADKResponsePart, log: ADKResponse) => void,
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
      msgCallback(eventData, eventLog);
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
 * @returns The extracted text as a string, or throws an error if error response detected
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

  // Check for structured error responses
  const allText = textSections.join("\n");
  if (allText.includes("MANUGEN_ERROR:")) {
    const errorMatch = allText.match(/MANUGEN_ERROR:\s*(\{.*?\})/);
    if (errorMatch) {
      try {
        const errorData = JSON.parse(errorMatch[1]);
        throw new ManugenError(
          errorData.error_type || 'unknown_error',
          errorData.message || 'An error occurred',
          errorData.details || '',
          errorData.suggestion || ''
        );
      } catch (e) {
        if (e instanceof ManugenError) {
          throw e;
        }
        // If JSON parsing fails, throw a generic error
        throw new ManugenError(
          'parse_error',
          'Failed to parse error response',
          'The server returned an error but it could not be parsed properly.',
          'Please try again or contact support if the problem persists.'
        );
      }
    }
  }

  if (onlyLast) {
    // if onlyLast is true, return the last text section
    return textSections.length > 0 ? textSections[textSections.length - 1] : "";
  }
  else {
    // if onlyLast is false, return all text sections concatenated
    return textSections.join("\n");
  }
}

/**
 * Custom error class for Manugen AI errors
 */
export class ManugenError extends Error {
  public readonly errorType: string;
  public readonly details: string;
  public readonly suggestion: string;

  constructor(errorType: string, message: string, details: string = '', suggestion: string = '') {
    super(message);
    this.name = 'ManugenError';
    this.errorType = errorType;
    this.details = details;
    this.suggestion = suggestion;
  }
}
