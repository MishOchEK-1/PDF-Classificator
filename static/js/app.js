const form = document.getElementById("classify-form");
const backendStatusNode = document.getElementById("backend-status");
const statusNode = document.getElementById("status");
const resultNode = document.getElementById("result");
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

form?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const file = formData.get("file");

  if (!(file instanceof File) || !file.name) {
    statusNode.textContent = "Select a PDF file before submitting.";
    return;
  }

  submitButton?.setAttribute("disabled", "disabled");
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
    resultNode.textContent = JSON.stringify(payload, null, 2);
    statusNode.textContent = response.ok
      ? "Document processed successfully."
      : "Backend responded. The classification pipeline is not fully implemented yet.";
  } catch (error) {
    statusNode.textContent = "Unable to reach the backend.";
    resultNode.textContent = JSON.stringify(
      { error: error instanceof Error ? error.message : "Unknown error" },
      null,
      2
    );
  } finally {
    submitButton?.removeAttribute("disabled");
  }
});
