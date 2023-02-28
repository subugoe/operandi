package main

import (
	"net/http"

	"github.com/labstack/echo/v4"
)

func main() {
	// Echo instance
	e := echo.New()

	// Routes
	e.GET("/broker", broker)
	e.GET("/server", server)

	// Start server
	e.Logger.Fatal(e.Start(":1323"))
}

// Handler
func broker(c echo.Context) error {
	return c.String(http.StatusOK, "Hello, broker!")
}

// Handler
func server(c echo.Context) error {
	return c.String(http.StatusOK, "Hello, Server!")
}
