const filterInput = document.querySelector("#filter-input");
const projectCards = Array.from(document.querySelectorAll(".projects-grid .card"));
const projectCount = document.querySelector("#project-count");

function updateProjects() {
    const query = filterInput.value.trim().toLocaleLowerCase();
    let visibleCount = 0;

    projectCards.forEach((card) => {
        const matches = card.textContent.toLocaleLowerCase().includes(query);
        card.classList.toggle("hidden", !matches);
        if (matches) {
            visibleCount += 1;
        }
    });

    projectCount.textContent = `Showing ${visibleCount} of ${projectCards.length} projects`;
}

filterInput.addEventListener("input", updateProjects);
updateProjects();
