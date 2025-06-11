const download = (url: string, filename: string, ext: string) => {
  if (!filename.endsWith("." + ext)) filename += "." + ext;
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(url);
};

export const getUrl = (data: BlobPart, type: string) =>
  typeof data === "string" && data.startsWith("data:")
    ? data
    : window.URL.createObjectURL(new Blob([data], { type }));

export const downloadTxt = (data: string, filename: string) =>
  download(getUrl(data, "text/plain;charset=utf-8"), filename, "txt");
