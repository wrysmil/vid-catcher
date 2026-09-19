function pad(n, width = 2) {
  return String(n).padStart(width, "0");
}

export function formatSrtTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  return `${pad(h)}:${pad(m)}:${pad(s)},${pad(ms, 3)}`;
}

export function formatVttTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  return `${pad(h)}:${pad(m)}:${pad(s)}.${pad(ms, 3)}`;
}

export function segmentsToSrt(segments) {
  return segments
    .map((seg, i) => {
      const start = formatSrtTime(seg.start);
      const end = formatSrtTime(seg.end);
      return `${i + 1}\n${start} --> ${end}\n${seg.text}\n`;
    })
    .join("\n");
}

export function segmentsToVtt(segments) {
  const body = segments
    .map((seg) => `${formatVttTime(seg.start)} --> ${formatVttTime(seg.end)}\n${seg.text}\n`)
    .join("\n");
  return `WEBVTT\n\n${body}`;
}

export function segmentsToTxt(segments) {
  return segments.map((seg) => seg.text).join("\n");
}

export function safeDownloadName(title, fallback = "视频") {
  return (title || fallback).replace(/[\\/*?:"<>|]/g, "_").slice(0, 80);
}

export function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function buildSubtitleBlob(segments, format) {
  if (format === "srt") {
    return { content: segmentsToSrt(segments), ext: "srt" };
  }
  if (format === "vtt") {
    return { content: segmentsToVtt(segments), ext: "vtt" };
  }
  return { content: segmentsToTxt(segments), ext: "txt" };
}
