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
)

type Chunk struct {
	ID        string `json:"id"`
	Text      string `json:"text"`
	Start     int    `json:"start"`
	End       int    `json:"end"`
	Language  string `json:"language"`
}

type IngestResponse struct {
	Chunks []Chunk `json:"chunks"`
	Text   string  `json:"text,omitempty"`
}

func detectLanguage(s string) string {
	// simple heuristic: detect ascii/latin words
	ascii := regexp.MustCompile(`^[\x00-\x7F]+$`).MatchString
	if ascii(s) {
		return "en"
	}
	return "auto"
}

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
	path := filepath.Join(tmpDir, header.Filename)
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

func extractText(path string) (string, error) {
	exe := "python"
	script := ".\\app\\utils\\extract.py"
	if _, err := os.Stat(script); os.IsNotExist(err) {
		script = "app/utils/extract.py"
	}
	cmd := exec.Command(exe, script, "--file", path)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("extract failed: %v: %s", err, string(out))
	}
	var data struct{ Text string `json:"text"` }
	if err := json.Unmarshal(out, &data); err != nil {
		return "", err
	}
	return data.Text, nil
}

func ingestHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte(`{"error":"method_not_allowed"}`))
		return
	}
	var text string
	file, header, err := r.FormFile("file")
	if err == nil {
		defer file.Close()
		path, err := saveUploadedFile(file, header)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte(`{"error":"upload_failed"}`))
			return
		}
		text, err = extractText(path)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			w.Write([]byte(fmt.Sprintf(`{"error":"extract_failed","detail":%q}`, err.Error())))
			return
		}
	} else {
		// maybe text in form
		if err := r.ParseForm(); err == nil {
			text = r.FormValue("text")
		}
	}
	text = strings.TrimSpace(text)
	if text == "" {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(`{"error":"no_input"}`))
		return
	}
	chs := chunkText(text, 1200, 200)
	res := IngestResponse{Chunks: chs, Text: text}
	enc := json.NewEncoder(w)
	enc.Encode(res)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{"status":"ok"}`))
}

func main() {
	port := os.Getenv("PORT")
	if port == "" { port = "8090" }
	http.HandleFunc("/ingest", ingestHandler)
	http.HandleFunc("/health", healthHandler)
	log.Printf("Go ingest service listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
