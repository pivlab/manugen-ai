/** download url */
const download = (url: string, filename: string, ext: string) => {
  if (!filename.endsWith("." + ext)) filename += "." + ext;
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
};

/** create blob url */
export const getUrl = (data: BlobPart, type: string) =>
  typeof data === "string" && data.startsWith("data:")
    ? data
    : window.URL.createObjectURL(new Blob([data], { type }));

/** download text data */
export const downloadMd = (data: string, filename: string) =>
  download(getUrl(data, "text/markdown;charset=utf-8"), filename, "md");
