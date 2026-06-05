const form = document.getElementById("classify-form");
const fileInput = document.getElementById("pdf-file");
const dropZone = document.getElementById("drop-zone");
const uploadCaptionNode = document.getElementById("upload-caption");
const backendStatusNode = document.getElementById("backend-status");
const statusNode = document.getElementById("status");
const loadingIndicatorNode = document.getElementById("loading-indicator");
const loadingLabelNode = document.getElementById("loading-label");
const progressFillNode = document.getElementById("progress-fill");
const progressValueNode = document.getElementById("progress-value");
const resultClassNode = document.getElementById("result-class");
const resultConfidenceNode = document.getElementById("result-confidence");
const resultTagsNode = document.getElementById("result-tags");
const resultErrorTypeNode = document.getElementById("result-error-type");
const resultErrorNode = document.getElementById("result-error");
const submitButton = form?.querySelector("button[type='submit']");
const progressTrackNode = document.querySelector(".progress-track");

const stageNodes = {
  upload: document.getElementById("stage-upload"),
  processing: document.getElementById("stage-processing"),
  inference: document.getElementById("stage-inference"),
};

const csrfToken = form?.querySelector("input[name='csrfmiddlewaretoken']")?.value ?? "";

let inferenceTimerId = null;

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

function setUploadCaption(fileName) {
  if (!uploadCaptionNode) {
    return;
  }

  uploadCaptionNode.textContent = fileName
    ? `Selected file: ${fileName}`
    : "Drag and drop a PDF here, or click to browse from your device.";
}

function setLoadingState(isLoading, label = "Uploading PDF...") {
  submitButton?.toggleAttribute("disabled", isLoading);

  if (loadingIndicatorNode) {
    loadingIndicatorNode.hidden = !isLoading;
  }

  if (loadingLabelNode) {
    loadingLabelNode.textContent = label;
  }
}

function setProgress(percent) {
  const safePercent = Math.max(0, Math.min(100, Math.round(percent)));

  if (progressFillNode) {
    progressFillNode.style.width = `${safePercent}%`;
  }

  if (progressValueNode) {
    progressValueNode.textContent = `${safePercent}%`;
  }

  if (progressTrackNode) {
    progressTrackNode.setAttribute("aria-valuenow", String(safePercent));
  }
}

function setActiveStage(stage) {
  Object.entries(stageNodes).forEach(([name, node]) => {
    if (!node) {
      return;
    }

    node.classList.remove("stage-pill-active", "stage-pill-done");

    if (name === stage) {
      node.classList.add("stage-pill-active");
      return;
    }

    if (
      (stage === "processing" && name === "upload") ||
      (stage === "inference" && (name === "upload" || name === "processing"))
    ) {
      node.classList.add("stage-pill-done");
    }
  });
}

function resetPipelineState() {
  clearInferenceTimer();
  setProgress(0);
  setActiveStage(null);
  setLoadingState(false, "Uploading PDF...");
}

function clearInferenceTimer() {
  if (inferenceTimerId !== null) {
    clearTimeout(inferenceTimerId);
    inferenceTimerId = null;
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

function renderResult(payload, errorType = "No active error category.", errorMessage = "No errors.") {
  const classification = payload?.class ?? "unknown";
  const confidence = payload?.confidence ?? "n/a";
  const tags = payload?.tags ?? [];

  if (resultClassNode) {
    resultClassNode.textContent = String(classification);
  }

  if (resultConfidenceNode) {
    resultConfidenceNode.textContent =
      typeof confidence === "number" ? confidence.toFixed(2) : String(confidence);
  }

  renderTags(tags);

  if (resultErrorTypeNode) {
    resultErrorTypeNode.textContent = errorType;
  }

  if (resultErrorNode) {
    resultErrorNode.textContent = errorMessage;
  }
}

function getErrorPresentation(statusCode, payload) {
  const detail = payload?.detail || "Unexpected API error.";

  if (statusCode === 400) {
    const validationMessage = payload?.file?.[0] || detail;
    return {
      errorType: "Invalid PDF",
      errorMessage: validationMessage,
      statusMessage: "The uploaded file was rejected before processing.",
    };
  }

  if (statusCode === 422) {
    return {
      errorType: "Parsing Error",
      errorMessage: detail,
      statusMessage: "PDF parsing completed with no usable text output.",
    };
  }

  if (statusCode === 503) {
    return {
      errorType: "Ollama Error",
      errorMessage: detail,
      statusMessage: "The local model runtime is currently unavailable.",
    };
  }

  if (statusCode === 504) {
    return {
      errorType: "Timeout Error",
      errorMessage: detail,
      statusMessage: "Inference took too long and the request timed out.",
    };
  }

  if (statusCode === 502) {
    return {
      errorType: "Model Response Error",
      errorMessage: detail,
      statusMessage: "The backend received an unusable response from the model.",
    };
  }

  return {
    errorType: "API Error",
    errorMessage: detail,
    statusMessage: "The backend returned an unexpected error.",
  };
}

function attachDropZoneBehavior() {
  if (!dropZone || !fileInput) {
    return;
  }

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

function classifyDocument(formData) {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();

    request.open("POST", "/api/classify/");
    request.responseType = "json";
    request.setRequestHeader("X-CSRFToken", csrfToken);

    request.upload.onprogress = (event) => {
      if (!event.lengthComputable) {
        return;
      }

      const percent = (event.loaded / event.total) * 100;
      setActiveStage("upload");
      setLoadingState(true, "Uploading PDF...");
      setProgress(percent);
      statusNode.textContent = `Uploading PDF... ${Math.round(percent)}%`;
    };

    request.upload.onload = () => {
      setActiveStage("processing");
      setLoadingState(true, "Processing PDF...");
      setProgress(100);
      statusNode.textContent = "Upload complete. Processing PDF text...";

      clearInferenceTimer();
      inferenceTimerId = window.setTimeout(() => {
        setActiveStage("inference");
        setLoadingState(true, "Running model inference...");
        statusNode.textContent = "PDF processed. Running local model inference...";
      }, 350);
    };

    request.onload = () => {
      clearInferenceTimer();
      const payload = request.response ?? safelyParseJson(request.responseText);
      resolve({ status: request.status, payload });
    };

    request.onerror = () => {
      clearInferenceTimer();
      reject(new Error("Network error while contacting the backend."));
    };

    request.ontimeout = () => {
      clearInferenceTimer();
      reject(new Error("The browser request timed out."));
    };

    request.send(formData);
  });
}

function safelyParseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

loadBackendStatus();
resetPipelineState();
attachDropZoneBehavior();

fileInput?.addEventListener("change", () => {
  setUploadCaption(fileInput.files?.[0]?.name ?? "");
});

form?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const file = formData.get("file");

  if (!(file instanceof File) || !file.name) {
    statusNode.textContent = "Select a PDF file before submitting.";
    renderResult({}, "Invalid PDF", "No file was selected.");
    return;
  }

  renderResult({}, "No active error category.", "No errors.");
  setActiveStage("upload");
  setLoadingState(true, "Uploading PDF...");
  setProgress(0);

  try {
    const { status, payload } = await classifyDocument(formData);

    if (status >= 200 && status < 300) {
      clearInferenceTimer();
      setActiveStage("inference");
      setLoadingState(false, "Uploading PDF...");
      statusNode.textContent = "Classification completed successfully.";
      renderResult(payload, "No errors.", "No errors.");
      return;
    }

    const { errorType, errorMessage, statusMessage } = getErrorPresentation(status, payload);
    setLoadingState(false, "Uploading PDF...");
    statusNode.textContent = statusMessage;
    renderResult({}, errorType, errorMessage);
  } catch (error) {
    setLoadingState(false, "Uploading PDF...");
    statusNode.textContent = "Unable to reach the backend.";
    renderResult(
      {},
      "Connection Error",
      error instanceof Error ? error.message : "Unknown network error."
    );
  }
});
