package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

type Chunk struct {
	ID       string `json:"id"`
	Text     string `json:"text"`
	Start    int    `json:"start"`
	End      int    `json:"end"`
	Language string `json:"language"`
}

type IngestResponse struct {
	Chunks []Chunk `json:"chunks"`
	Text   string  `json:"text,omitempty"`
}

// detectLanguage: very simple heuristic for demo
func detectLanguage(s string) string {
	ascii := regexp.MustCompile(`^[\x00-\x7F\s\p{P}]+$`).MatchString
	if ascii(s) {
		return "en"
	}
	return "auto"
}

// chunkText: chunk by bytes (simple, fast). size = bytes per chunk, overlap = bytes overlapped
func chunkText(s string, size int, overlap int) []Chunk {
	chunks := []Chunk{}
	i := 0
	n := len(s)
	id := 0
	for i < n {
		j := i + size
		if j > n {
			j = n
		}
		ch := s[i:j]
		chunks = append(chunks, Chunk{
			ID:       fmt.Sprintf("c-%d", id),
			Text:     ch,
			Start:    i,
			End:      j,
			Language: detectLanguage(ch),
		})
		id++
		i = j - overlap
		if i < 0 {
			i = 0
		}
	}
	return chunks
}

func saveUploadedFile(file multipart.File, header *multipart.FileHeader) (string, error) {
	tmpDir := os.TempDir()
	path := filepath.Join(tmpDir, fmt.Sprintf("%d_%s", time.Now().UnixNano(), header.Filename))
	out, err := os.Create(path)
	if err != nil {
		return "", err
	}
	defer out.Close()
	_, err = io.Copy(out, file)
	if err != nil {
		return "", err
	}
	return path, nil
}

// findExtractor tries possible locations for the python extractor script.
// returns full path to script or empty string
func findExtractor() string {
	candidates := []string{
		"./app/utils/extract.py",    // repo root (Windows)
		"app/utils/extract.py",      // repo root (Linux)
		"/app/app/utils/extract.py", // Dockerfile copies to /app/app/utils
		filepath.Join(".", "app", "utils", "extract.py"),
	}
	for _, p := range candidates {
		if _, err := os.Stat(p); err == nil {
			abs, _ := filepath.Abs(p)
			return abs
		}
	}
	return ""
}

func findPythonExec() string {
	// try python3 then python; fallback to "python"
	cands := []string{"python3", "python"}
	for _, c := range cands {
		if path, err := exec.LookPath(c); err == nil {
			return path
		} else {
			_ = path // ignore
		}
	}
	return "python"
}

func extractText(path string) (string, error) {
	script := findExtractor()
	if script == "" {
		return "", fmt.Errorf("extractor script not found; expected app/utils/extract.py")
	}

	py := findPythonExec()
	cmd := exec.Command(py, script, "--file", path)
	// ensure environment PATH available in Docker too
	cmd.Env = os.Environ()
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("extract failed: %v: %s", err, string(out))
	}
	var data struct {
		Text string `json:"text"`
	}
	if err := json.Unmarshal(out, &data); err != nil {
		// return raw output in error detail to help debug
		return "", fmt.Errorf("invalid extractor output: %v: %s", err, string(out))
	}
	return data.Text, nil
}

func writeJSON(w http.ResponseWriter, v interface{}, code int) {
	w.Header().Set("Content-Type", "application/json")
	// simple demo CORS
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func ingestHandler(w http.ResponseWriter, r *http.Request) {
	// debug log: incoming request
	log.Printf("incoming %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

	// handle CORS preflight
	if r.Method == http.MethodOptions {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		writeJSON(w, map[string]string{"error": "method_not_allowed"}, http.StatusMethodNotAllowed)
		return
	}

	// parse form but not require file
	if err := r.ParseMultipartForm(32 << 20); err != nil && err != http.ErrNotMultipart {
		// for non-multipart POSTs this may be fine; keep simple error handling
		// continue
	}

	var text string
	file, header, err := r.FormFile("file")
	if err == nil {
		defer file.Close()
		path, err := saveUploadedFile(file, header)
		if err != nil {
			writeJSON(w, map[string]string{"error": "upload_failed", "detail": err.Error()}, http.StatusBadRequest)
			return
		}
		// attempt extraction
		text, err = extractText(path)
		// remove temp file (best-effort)
		_ = os.Remove(path)
		if err != nil {
			writeJSON(w, map[string]string{"error": "extract_failed", "detail": err.Error()}, http.StatusBadRequest)
			return
		}
	} else {
		// fallback: allow plain text in form field "text"
		if err := r.ParseForm(); err == nil {
			text = r.FormValue("text")
		}
	}

	text = strings.TrimSpace(text)
	if text == "" {
		writeJSON(w, map[string]string{"error": "no_input"}, http.StatusBadRequest)
		return
	}

	// chunk size and overlap in bytes (keeps logic compatible with earlier code)
	chunks := chunkText(text, 1200, 200)
	res := IngestResponse{Chunks: chunks, Text: ""} // avoid dumping full text by default
	writeJSON(w, res, http.StatusOK)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("incoming %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
	writeJSON(w, map[string]string{"status": "ok"}, http.StatusOK)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = os.Getenv("INGEST_PORT")
	}
	if port == "" {
		port = "8091"
	}

	// Helpful debug prints so you can see extractor and python choices at startup
	log.Printf("extractor candidate found at: %s", findExtractor())
	log.Printf("python binary candidate: %s", findPythonExec())

	http.HandleFunc("/ingest", ingestHandler)
	http.HandleFunc("/health", healthHandler)

	// simple ping endpoint for quick connectivity tests
	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("incoming %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("pong"))
	})

	log.Printf("Go ingest service listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
