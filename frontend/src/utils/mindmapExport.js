import { triggerDownload } from "./subtitleFormat.js";

export function getContentBBox(svgEl) {
  const fallback = { x: 0, y: 0, width: 800, height: 600 };
  if (!svgEl) return fallback;

  const gRoot = svgEl.querySelector("g");
  if (gRoot) {
    try {
      const bbox = gRoot.getBBox();
      if (bbox.width > 0 && bbox.height > 0) {
        const transform = gRoot.getAttribute("transform") || "";
        const translateMatch = transform.match(/translate\(\s*([-\d.e]+)\s*[,\s]\s*([-\d.e]+)\s*\)/);
        const scaleMatch = transform.match(/scale\(\s*([-\d.e]+)/);
        const tx = translateMatch ? parseFloat(translateMatch[1]) : 0;
        const ty = translateMatch ? parseFloat(translateMatch[2]) : 0;
        const sc = scaleMatch ? parseFloat(scaleMatch[1]) : 1;
        return {
          x: bbox.x * sc + tx,
          y: bbox.y * sc + ty,
          width: bbox.width * sc,
          height: bbox.height * sc,
        };
      }
    } catch {
      /* getBBox 在未插入文档时可能抛错 */
    }
  }

  try {
    const bbox = svgEl.getBBox();
    if (bbox.width > 0 && bbox.height > 0) return bbox;
  } catch {
    /* ignore */
  }
  return fallback;
}

function sanitizeTransforms(root) {
  root.querySelectorAll("[transform]").forEach((el) => {
    const t = el.getAttribute("transform");
    if (t && t.includes("NaN")) {
      el.setAttribute("transform", "translate(0,0) scale(1)");
    }
  });
}

export function buildExportableSvg(svgEl) {
  if (!svgEl) return null;
  const cloned = svgEl.cloneNode(true);
  sanitizeTransforms(cloned);

  cloned.querySelectorAll("foreignObject").forEach((fo) => {
    const textContent = fo.textContent?.trim() || "";
    if (!textContent) {
      fo.remove();
      return;
    }
    const x = parseFloat(fo.getAttribute("x")) || 0;
    const y = parseFloat(fo.getAttribute("y")) || 0;
    const h = parseFloat(fo.getAttribute("height")) || 20;
    const textEl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    textEl.setAttribute("x", String(x + 4));
    textEl.setAttribute("y", String(y + h / 2 + 5));
    textEl.setAttribute("font-size", "14");
    textEl.setAttribute("font-family", "sans-serif");
    textEl.setAttribute("fill", "#333");
    textEl.setAttribute("dominant-baseline", "middle");
    textEl.textContent = textContent;
    fo.parentNode.replaceChild(textEl, fo);
  });

  return cloned;
}

export function setFullViewBox(svgClone, svgEl) {
  const dims = getContentBBox(svgEl);
  const padding = 60;
  const vx = dims.x - padding;
  const vy = dims.y - padding;
  const vw = dims.width + padding * 2;
  const vh = dims.height + padding * 2;
  svgClone.setAttribute("viewBox", `${vx} ${vy} ${vw} ${vh}`);
  svgClone.setAttribute("width", String(vw));
  svgClone.setAttribute("height", String(vh));
  return { vw, vh };
}

export function serializeSvg(svgEl, extraCss = "") {
  const serializer = new XMLSerializer();
  let svgString = serializer.serializeToString(svgEl);
  if (!svgString.includes("xmlns=")) {
    svgString = svgString.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"');
  }
  if (extraCss && !svgString.includes("<style")) {
    svgString = svgString.replace(">", `><style>${extraCss}</style>`);
  }
  return svgString;
}

export async function downloadMindmapPng(svgEl, filename, extraCss = "") {
  const exportSvg = buildExportableSvg(svgEl);
  if (!exportSvg) return false;
  const { vw, vh } = setFullViewBox(exportSvg, svgEl);
  const scale = Math.max(4, Math.ceil(3840 / vw));
  const svgString = serializeSvg(exportSvg, extraCss);

  const canvas = document.createElement("canvas");
  canvas.width = vw * scale;
  canvas.height = vh * scale;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const img = new Image();
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  return new Promise((resolve) => {
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      canvas.toBlob((pngBlob) => {
        if (pngBlob) triggerDownload(pngBlob, filename);
        resolve(Boolean(pngBlob));
      }, "image/png");
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(false);
    };
    img.src = url;
  });
}

export function downloadMindmapSvg(svgEl, filename, extraCss = "") {
  if (!svgEl) return false;
  const cloned = svgEl.cloneNode(true);
  sanitizeTransforms(cloned);
  setFullViewBox(cloned, svgEl);
  const svgString = serializeSvg(cloned, extraCss);
  const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  triggerDownload(blob, filename);
  return true;
}
