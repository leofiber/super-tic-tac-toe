const boardContainer = document.getElementById("board");
const statusDisplay = document.getElementById("status");
let currentBoard = null;
let gameOver = false;
let aiThinking = false;
let legalMoves = [];

function renderBoard(board, smallStatus) {
  boardContainer.innerHTML = "";

  for (let bigRow = 0; bigRow < 3; bigRow++) {
    for (let bigCol = 0; bigCol < 3; bigCol++) {
      const smallBoard = document.createElement("div");
      
      // Check if this small board is won
      const smallBoardStatus = smallStatus[bigRow][bigCol];
      let boardClasses = "dev-small-board";
      
      if (smallBoardStatus === 1) {
        boardClasses += " won-x";
      } else if (smallBoardStatus === -1 || smallBoardStatus === 2) {
        boardClasses += " won-o";
      }
      
      // Add active class if this is the current board
      if (currentBoard && currentBoard[0] === bigRow && currentBoard[1] === bigCol) {
        boardClasses += " active";
      }
      
      smallBoard.className = boardClasses;

      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          const r = bigRow * 3 + i;
          const c = bigCol * 3 + j;
          const val = board[r][c];
          const cell = document.createElement("div");
          const isLegal = legalMoves.some(
            ([lr, lc]) => lr === r && lc === c
          );

          let cellClasses = "dev-cell";
          if (val === 1) {
            cellClasses += " player-x";
          } else if (val === -1) {
            cellClasses += " player-o";
          } else if (isLegal && !gameOver && !aiThinking) {
            cellClasses += " legal-move";
          }

          cell.className = cellClasses;
          cell.textContent = val === 1 ? "1" : val === -1 ? "0" : "";
          cell.dataset.row = r;
          cell.dataset.col = c;

          if (isLegal && !gameOver && !aiThinking) {
            cell.addEventListener("click", handleCellClick);
          }

          smallBoard.appendChild(cell);
        }
      }

      boardContainer.appendChild(smallBoard);
    }
  }
}

async function handleCellClick(e) {
  if (gameOver || aiThinking) return;

  const row = parseInt(e.currentTarget.dataset.row);
  const col = parseInt(e.currentTarget.dataset.col);

  try {
    const res = await fetch("/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ row, col }),
    });
    if (!res.ok) throw new Error(`Move failed: ${res.status}`);
    const data = await res.json();
    updateUI(data);

    if (!data.winner) {
      aiThinking = true;
      statusDisplay.textContent = "AI is thinking...";
      const aiRes = await fetch("/ai", { method: "POST" });
      if (!aiRes.ok) throw new Error(`AI move failed: ${aiRes.status}`);
      const aiData = await aiRes.json();
      aiThinking = false;
      updateUI(aiData);
    }
  } catch (err) {
    console.error(err);
  }
}

function updateUI(data) {
  const {
    board,
    small_status,
    current_board,
    legal_moves,
    winner
  } = data;

  legalMoves = legal_moves || [];
  currentBoard = current_board;
  renderBoard(board, small_status);

  if (winner === 1) {
    statusDisplay.textContent = "❌ Player (X) wins!";
    gameOver = true;
  } else if (winner === -1) {
    statusDisplay.textContent = "⭕ AI (O) wins!";
    gameOver = true;
  } else if (winner === 0 && board.flat().every((x) => x !== 0)) {
    statusDisplay.textContent = "🤝 It's a draw!";
    gameOver = true;
  } else if (!aiThinking) {
    statusDisplay.textContent = "";
  }
}

async function resetGame() {
  console.log("resetGame() called");
  gameOver = false;
  aiThinking = false;
  currentBoard = null;
  legalMoves = [];
  statusDisplay.textContent = "";
  try {
    const res = await fetch("/reset", { method: "POST" });
    if (!res.ok) throw new Error(`Reset failed: ${res.status}`);
    const data = await res.json();
    updateUI(data);
  } catch (err) {
    console.error(err);
    statusDisplay.textContent = "Error resetting game";
  }
}

// Attach listeners after DOM is ready
// and log to ensure scripts are running
console.log("game.js loaded");
document.addEventListener("DOMContentLoaded", () => {
  const resetBtn = document.getElementById("reset-btn");
  console.log("DOMContentLoaded: reset-btn =", resetBtn);
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      console.log("reset-btn clicked");
      resetGame();
    });
  }
  resetGame();
});