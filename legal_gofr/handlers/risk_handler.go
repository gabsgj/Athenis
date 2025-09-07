package handlers

import (
	"encoding/json"
	"net/http"
	"os/exec"
)

// RiskRequest is the input JSON
type RiskRequest struct {
	Text string `json:"text"`
}

// RiskAnalyzer handles POST /analyze
func RiskAnalyzer(w http.ResponseWriter, r *http.Request) {
	var req RiskRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid input", http.StatusBadRequest)
		return
	}

	// Call the Python script
	cmd := exec.Command("python", "risk_detector.py", req.Text)
    cmd.Dir = "C:\\Users\\Nayana\\Downloads\\legal_simplify\\hackOdisha\\app\\models"
	output, err := cmd.Output()
	if err != nil {
		http.Error(w, "Error running risk detector", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Write(output)
}
