const form = document.getElementById("classify-form");
const statusNode = document.getElementById("status");
const resultNode = document.getElementById("result");

form?.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);
  const file = formData.get("file");

  if (!(file instanceof File) || !file.name) {
    statusNode.textContent = "Select a PDF file before submitting.";
    return;
  }

  statusNode.textContent = "Sending the file to the backend...";

  try {
    const response = await fetch("/api/classify/", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    resultNode.textContent = JSON.stringify(payload, null, 2);
    statusNode.textContent = response.ok
      ? "Document processed successfully."
      : "Backend responded, but the full pipeline is not ready yet.";
  } catch (error) {
    statusNode.textContent = "Unable to reach the backend.";
    resultNode.textContent = JSON.stringify(
      { error: error instanceof Error ? error.message : "Unknown error" },
      null,
      2
    );
  }
});
