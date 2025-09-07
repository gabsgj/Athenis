package main

import (
	"legal_gofr/handlers"
	"os"

	"gofr.dev/pkg/gofr"
)

func main() {
	// Create a new GoFr app
	app := gofr.New()

	// Get script path from environment variable or use default
	pyScriptPath := os.Getenv("PY_EXTRACT_SCRIPT")
	if pyScriptPath == "" {
		// Default path within the container
		pyScriptPath = "/app/app/utils/extract.py"
	}

	// Create a handler with the script path
	h := handlers.New(pyScriptPath)

	// Register routes
	app.GET("/health", h.Health)
	app.POST("/ingest", h.Ingest)

	// Run the app
	app.Run()
}
