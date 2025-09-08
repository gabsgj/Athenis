package handlers

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"os/exec"

	"gofr.dev/pkg/gofr"
)

type handler struct {
	pyScriptPath string
}

// New creates a new handler with the given python script path
func New(pyScriptPath string) *handler {
	return &handler{pyScriptPath: pyScriptPath}
}

// Health is a simple health check endpoint
func (h *handler) Health(c *gofr.Context) (interface{}, error) {
	return map[string]bool{"ok": true}, nil
}

// Ingest handles file uploads, extracts text using a python script, and returns the text.
func (h *handler) Ingest(c *gofr.Context) (interface{}, error) {
	// Parse multipart form
	if err := c.Request.ParseMultipartForm(10 << 20); err != nil { // 10 MB
		return nil, gofr.NewError(http.StatusBadRequest, "Invalid file upload request")
	}

	file, _, err := c.Request.FormFile("file")
	if err != nil {
		return nil, gofr.NewError(http.StatusBadRequest, "Missing 'file' in form data")
	}
	defer file.Close()

	// Create a temporary file
	tempFile, err := os.CreateTemp("/tmp", "upload-*.tmp")
	if err != nil {
		return nil, gofr.NewError(http.StatusInternalServerError, "Could not create temporary file")
	}
	defer os.Remove(tempFile.Name())

	// Copy uploaded file to temporary file
	bytesCopied, err := io.Copy(tempFile, file)
	if err != nil {
		return nil, gofr.NewError(http.StatusInternalServerError, "Could not save uploaded file")
	}
	tempFile.Close() // Close so the python script can open it

	// Execute the python script
	cmd := exec.CommandContext(c.Request.Context(), "python", h.pyScriptPath, "--file", tempFile.Name())
	output, err := cmd.CombinedOutput()
	if err != nil {
		c.Logger.Errorf("Python script execution failed: %v, Output: %s", err, string(output))
		return nil, gofr.NewError(http.StatusInternalServerError, "Error running extraction script")
	}

	// Parse the JSON output from the Python script
	var extractResult struct {
		Text  string `json:"text"`
		Error string `json:"error"`
	}
	
	if err := json.Unmarshal(output, &extractResult); err != nil {
		c.Logger.Errorf("Failed to parse Python script output: %v", err)
		return nil, gofr.NewError(http.StatusInternalServerError, "Invalid extraction output format")
	}
	
	if extractResult.Error != "" {
		return nil, gofr.NewError(http.StatusBadRequest, "Extraction failed: "+extractResult.Error)
	}

	return map[string]interface{}{
		"ok":    true,
		"text":  extractResult.Text,
		"bytes": bytesCopied,
	}, nil
}
