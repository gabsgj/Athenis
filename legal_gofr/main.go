package main

import (
	"log"
	"net/http"

	"legal_gofr/handlers"
)

func main() {
	http.HandleFunc("/analyze", handlers.RiskAnalyzer)

	log.Println("Server running at http://localhost:8080")
	err := http.ListenAndServe(":8080", nil)
	if err != nil {
		log.Fatal(err)
	}
}
