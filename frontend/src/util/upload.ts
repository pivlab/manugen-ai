import { extractRawText } from "mammoth";
import * as pdfjs from "pdfjs-dist";
import workerSrc from "pdfjs-dist/build/pdf.worker?url";

pdfjs.GlobalWorkerOptions.workerSrc = workerSrc;

export const parseWordDoc = async (buffer: ArrayBuffer) =>
  (await extractRawText({ arrayBuffer: buffer })).value;

export const parsePdf = async (buffer: ArrayBuffer) => {
  const pdf = await pdfjs.getDocument(buffer).promise;
  let text = "";
  for (let pageIndex = 1; pageIndex <= pdf.numPages; pageIndex++)
    text +=
      (await (await pdf.getPage(pageIndex)).getTextContent()).items
        .map((item) => ("str" in item ? item.str : ""))
        .join(" ") + "\n";
  return text;
};
