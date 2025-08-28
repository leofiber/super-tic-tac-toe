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
      smallBoard.className =
        "grid grid-cols-3 gap-[2px] border-4 rounded-lg p-[2px] " +
        (currentBoard && currentBoard[0] === bigRow && currentBoard[1] === bigCol
          ? "border-yellow-400"
          : "border-gray-500");

      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          const r = bigRow * 3 + i;
          const c = bigCol * 3 + j;
          const val = board[r][c];
          const cell = document.createElement("div");
          const isLegal = legalMoves.some(
            ([lr, lc]) => lr === r && lc === c
          );

          cell.className =
            "w-10 h-10 flex items-center justify-center text-lg font-bold rounded " +
            (val === 1
              ? "text-blue-400 bg-gray-800"
              : val === -1
              ? "text-red-400 bg-gray-800"
              : isLegal
              ? "bg-yellow-300 text-black cursor-pointer hover:bg-yellow-400"
              : "bg-gray-700 text-gray-500 cursor-not-allowed");
          cell.textContent = val === 1 ? "X" : val === -1 ? "O" : "";
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