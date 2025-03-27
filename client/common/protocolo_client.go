package common

import (
	"bufio"
	"fmt"
	"strings"
)

func (c *Client) receiveWinners() error {
	winnersMessage, err := bufio.NewReader(c.conn).ReadString('\n')
	if err != nil {
		return fmt.Errorf("error receiving winners: %w", err)
	}

	winnersMessage = strings.TrimSpace(winnersMessage)

	const prefix = "GANADORES: "
	if !strings.HasPrefix(winnersMessage, prefix) {
		return fmt.Errorf("unexpected winners message format: %s", winnersMessage)
	}

	winnersList := strings.TrimSpace(strings.TrimPrefix(winnersMessage, prefix))

	if winnersList == "None" {
		winnersList = ""
	}

	var winnersArray []string
	if winnersList != "" {
		winnersArray = strings.Split(winnersList, " ,")
	}

	log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d", len(winnersArray))

	return nil
}
