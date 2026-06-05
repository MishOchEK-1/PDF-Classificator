const form = document.getElementById("classify-form");
const fileInput = document.getElementById("pdf-file");
const dropZone = document.getElementById("drop-zone");
const uploadCaptionNode = document.getElementById("upload-caption");
const backendStatusNode = document.getElementById("backend-status");
const statusNode = document.getElementById("status");
const loadingIndicatorNode = document.getElementById("loading-indicator");
const resultClassNode = document.getElementById("result-class");
const resultConfidenceNode = document.getElementById("result-confidence");
const resultTagsNode = document.getElementById("result-tags");
const resultErrorNode = document.getElementById("result-error");
const submitButton = form?.querySelector("button[type='submit']");

const csrfToken = form?.querySelector("input[name='csrfmiddlewaretoken']")?.value ?? "";

async function loadBackendStatus() {
  if (!backendStatusNode) {
    return;
  }

  try {
    const response = await fetch("/api/health/");
    const payload = await response.json();

    backendStatusNode.textContent = response.ok
      ? `Connected: ${payload.service}`
      : "Connected, but health check returned an error.";
  } catch {
    backendStatusNode.textContent = "Unable to reach the backend health endpoint.";
  }
}

loadBackendStatus();

function setUploadCaption(fileName) {
  if (!uploadCaptionNode) {
    return;
  }

  uploadCaptionNode.textContent = fileName
    ? `Selected file: ${fileName}`
    : "Drag and drop a PDF here, or click to browse from your device.";
}

function setLoadingState(isLoading) {
  submitButton?.toggleAttribute("disabled", isLoading);

  if (loadingIndicatorNode) {
    loadingIndicatorNode.hidden = !isLoading;
  }
}

function renderTags(tags) {
  if (!resultTagsNode) {
    return;
  }

  resultTagsNode.innerHTML = "";

  if (!Array.isArray(tags) || tags.length === 0) {
    const emptyChip = document.createElement("span");
    emptyChip.className = "tag-chip tag-chip-muted";
    emptyChip.textContent = "No tags";
    resultTagsNode.append(emptyChip);
    return;
  }

  tags.forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "tag-chip";
    chip.textContent = String(tag);
    resultTagsNode.append(chip);
  });
}

function renderResult(payload, errorMessage = "") {
  const classification = payload?.class ?? payload?.expected_response?.class ?? "unknown";
  const confidence = payload?.confidence ?? payload?.expected_response?.confidence ?? "n/a";
  const tags = payload?.tags ?? payload?.expected_response?.tags ?? [];

  if (resultClassNode) {
    resultClassNode.textContent = String(classification);
  }

  if (resultConfidenceNode) {
    resultConfidenceNode.textContent =
      typeof confidence === "number" ? confidence.toFixed(2) : String(confidence);
  }

  renderTags(tags);

  if (resultErrorNode) {
    resultErrorNode.textContent = errorMessage || "No errors.";
  }
}

fileInput?.addEventListener("change", () => {
  setUploadCaption(fileInput.files?.[0]?.name ?? "");
});

if (dropZone && fileInput) {
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropZone.classList.add("upload-field-dragover");
    });
  });

  ["dragleave", "dragend", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      if (eventName !== "drop") {
        dropZone.classList.remove("upload-field-dragover");
      }
    });
  });

  dropZone.addEventListener("drop", (event) => {
    const file = event.dataTransfer?.files?.[0];
    dropZone.classList.remove("upload-field-dragover");

    if (!file) {
      return;
    }

    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    setUploadCaption(file.name);
    statusNode.textContent = "PDF ready for upload.";
  });
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const file = formData.get("file");

  if (!(file instanceof File) || !file.name) {
    statusNode.textContent = "Select a PDF file before submitting.";
    return;
  }

  setLoadingState(true);
  statusNode.textContent = "Sending the file to the classification API...";

  try {
    const response = await fetch("/api/classify/", {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": csrfToken,
      },
      credentials: "same-origin",
    });

    const payload = await response.json();
    renderResult(payload, response.ok ? "" : payload.detail || "Classification is not ready yet.");
    statusNode.textContent = response.ok
      ? "Document processed successfully."
      : "Backend responded. The classification pipeline is not fully implemented yet.";
  } catch (error) {
    statusNode.textContent = "Unable to reach the backend.";
    renderResult({}, error instanceof Error ? error.message : "Unknown error");
  } finally {
    setLoadingState(false);
  }
});
