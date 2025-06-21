import type { SSE } from "sse.js";

export async function waitForEventSourceToClose(source: SSE) {
  return new Promise((resolve, reject) => {
    const handler = (event:any) => {
      if (event.readyState === 2) { // CLOSED
        source.removeEventListener('readystatechange', handler);
        resolve(true); // This will resume the async function
      }
    };

    source.addEventListener('readystatechange', handler);

    // Optionally add error handling
    source.addEventListener('error', (err:any) => {
      source.removeEventListener('readystatechange', handler);
      reject(err);
    });
  });
}
