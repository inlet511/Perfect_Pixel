const $ = (id) => document.getElementById(id);

const fileInput = $("file");
const statusEl = $("status");
const btnPreview = $("btn-preview");
const btnProcess = $("btn-process");

// Show original image locally when a file is picked.
fileInput.addEventListener("change", () => {
  const f = fileInput.files[0];
  if (f) {
    $("img-original").src = URL.createObjectURL(f);
    $("img-preview").src = "";
    $("img-result").src = "";
    $("detected").textContent = "";
    $("result-size").textContent = "";
    $("download-card").style.display = "none";
  }
});

// Toggle manual grid fields.
document.querySelectorAll('input[name="mode"]').forEach((r) => {
  r.addEventListener("change", updateMode);
});
function updateMode() {
  const manual = document.querySelector('input[name="mode"]:checked').value === "manual";
  $("manual-fields").classList.toggle("hidden", !manual);
  $("refine-row").classList.toggle("hidden", manual);
}
updateMode();

// Live label for the slider.
$("refine_intensity").addEventListener("input", (e) => {
  $("ri_val").textContent = Number(e.target.value).toFixed(2);
});

// Toggle background-removal tolerance row.
$("remove_bg").addEventListener("change", (e) => {
  $("bg-tolerance-row").classList.toggle("hidden", !e.target.checked);
});

// Live label for the tolerance slider.
$("bg_tolerance").addEventListener("input", (e) => {
  $("bt_val").textContent = e.target.value;
});

function buildFormData() {
  const f = fileInput.files[0];
  if (!f) {
    setStatus("请先选择一张图片", true);
    return null;
  }
  const fd = new FormData();
  fd.append("image", f);
  const mode = document.querySelector('input[name="mode"]:checked').value;
  fd.append("mode", mode);
  fd.append("grid_w", $("grid_w").value);
  fd.append("grid_h", $("grid_h").value);
  fd.append("refine_intensity", $("refine_intensity").value);
  fd.append("sample_method", $("sample_method").value);
  fd.append("export_scale", $("export_scale").value);
  fd.append("remove_bg", $("remove_bg").checked ? "true" : "false");
  fd.append("bg_tolerance", $("bg_tolerance").value);
  return fd;
}

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
}

function setBusy(busy) {
  btnPreview.disabled = busy;
  btnProcess.disabled = busy;
}

async function postForm(url, fd) {
  const resp = await fetch(url, { method: "POST", body: fd });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data.error || `请求失败 (${resp.status})`);
  }
  return data;
}

btnPreview.addEventListener("click", async () => {
  const fd = buildFormData();
  if (!fd) return;
  setBusy(true);
  setStatus("正在生成网格预览…");
  try {
    const data = await postForm("/preview", fd);
    $("img-preview").src = data.preview;
    if (data.detected) {
      $("detected").textContent = `(${data.detected[0]}×${data.detected[1]})`;
    }
    setStatus("预览完成");
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    setBusy(false);
  }
});

btnProcess.addEventListener("click", async () => {
  const fd = buildFormData();
  if (!fd) return;
  setBusy(true);
  setStatus("正在处理…");
  try {
    const data = await postForm("/process", fd);
    $("img-result").src = data.result_scaled;
    $("result-size").textContent = `(${data.width}×${data.height})`;
    $("dl-original").href = data.result;
    $("dl-scaled").href = data.result_scaled;
    $("download-card").style.display = "";
    setStatus("处理完成");
  } catch (err) {
    setStatus(err.message, true);
  } finally {
    setBusy(false);
  }
});
