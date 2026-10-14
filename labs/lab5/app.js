const filterInput = document.querySelector("#filter-input");
const projectCards = Array.from(document.querySelectorAll(".projects-grid .card"));
const projectCount = document.querySelector("#project-count");

function updateProjects() {
    const query = filterInput.value.trim().toLocaleLowerCase();
    let visibleCount = 0;

    projectCards.forEach((card) => {
        //hand-edited by AB//
        const matches = card.textContent.toLowerCase().includes(query);
        card.classList.toggle("is.hidden", !matches);
        if (matches) {
            visibleCount += 1;
        }
    });

    projectCount.textContent = `Showing ${visibleCount} of ${projectCards.length} projects`;
}

filterInput.addEventListener("input", updateProjects);
updateProjects();
