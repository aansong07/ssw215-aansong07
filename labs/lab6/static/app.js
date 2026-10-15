const filterInput = document.querySelector("#filter-input");
const projectCards = Array.from(document.querySelectorAll(".projects-grid .card"));
const projectCount = document.querySelector("#project-count");

function updateProjects() {
    const query = filterInput.value.trim().toLowerCase();
    let visibleCount = 0;
    const visibleProjectTitles = [];

    projectCards.forEach((card) => {
        const matches = card.textContent.toLowerCase().includes(query.toLowerCase());
        card.classList.toggle("hidden", !matches);
        if (matches) {
            visibleCount += 1;
            visibleProjectTitles.push(card.querySelector("h3").textContent.trim());
        }
    });

    projectCount.textContent = `Showing ${visibleCount} of ${projectCards.length} projects`;
    console.log(visibleProjectTitles);
}

filterInput.addEventListener("input", updateProjects);
updateProjects();
