document.addEventListener("DOMContentLoaded", function () {
    const picks = [
        { name: "Jeremiah Smith", position: "WR", college: "Ohio State" },
        { name: "Darius Taylor", position: "RB", college: "Minnesota" },
        { name: "Desmond Reid", position: "RB", college: "Pittsburgh" },
        { name: "Makhi Hughes", position: "RB", college: "Oregon" },
        { name: "Jordyn Tyson", position: "WR", college: "Arizona State" },
        { name: "Bryson Washington", position: "RB", college: "Baylor" }
    ];

    const pickCells = document.querySelectorAll(".pick-cell");
    let i = 0;
    const round = 1;  // since you’re only doing round 1 for now

    function showNextPick() {
        if (i < picks.length) {
            const player = picks[i];
            const cell = pickCells[i];

            // Set background color directly
            if (player.position === "WR") {
                cell.style.backgroundColor = "#6fff71";
            } else if (player.position === "RB") {
                cell.style.backgroundColor = "#6fe3ff";
            }

            // Create and insert team logo
            const teamLogo = document.createElement("img");
            const teamSlug = player.college.toLowerCase().replace(/\s+/g, "_"); // e.g., "Ohio State" → "ohio_state"
            teamLogo.src = `/static/images/teams/${teamSlug}.png`;
            teamLogo.alt = `${player.college} logo`;
            teamLogo.classList.add("team-logo");
            cell.appendChild(teamLogo);

            // Set pick number
            cell.querySelector('.pick-number').textContent = `${round}.${i + 1}`;

            // Split and set name
            const [firstName, ...rest] = player.name.split(" ");
            const lastName = rest.join(" ");
            cell.querySelector('.player-name').innerHTML = `
                <div class="first-name">${firstName}</div>
                <div class="last-name">${lastName}</div>
            `;

            // Set player info
            cell.querySelector('.player-info').textContent = `${player.position} - ${player.college}`;

            i++;
        }
    }


    const pickInterval = setInterval(() => {
        if (i < picks.length) {
            showNextPick();
        } else {
            clearInterval(pickInterval);
        }
    }, 3000);
});
