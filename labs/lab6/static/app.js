const filterInput = document.querySelector("#filter-input");
const projectCards = Array.from(document.querySelectorAll(".projects-grid .card"));
const projectCount = document.querySelector("#project-count");
const upvoteButtons = document.querySelectorAll(".upvote-btn");

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

upvoteButtons.forEach((button) => {
    button.addEventListener("click", async (event) => {
        const upvoteButton = event.currentTarget;
        const card = upvoteButton.closest(".card");
        const projectId = card.dataset.projectId;

        upvoteButton.disabled = true;
        try {
            const response = await fetch(`/api/projects/${projectId}/upvote`, {
                method: "POST",
            });
            if (!response.ok) {
                throw new Error(`Upvote failed with status ${response.status}`);
            }

            const result = await response.json();
            if (!Number.isInteger(result.likes)) {
                throw new Error("Upvote response did not contain a valid like count");
            }

            card.querySelector(".like-count").textContent = result.likes;
        } catch (error) {
            console.error("Unable to upvote project:", error);
        } finally {
            upvoteButton.disabled = false;
        }
    });
});
