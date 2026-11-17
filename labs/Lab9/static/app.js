const filterInput = document.querySelector("#filter-input");
const projectCount = document.querySelector("#project-count");
const projectsGrid = document.querySelector(".projects-grid");
const newProjectForm = document.querySelector("#new-project-form");
const newTitleInput = document.querySelector("#new-title");
const createProjectMessage = document.querySelector("#create-project-message");
const smartProjectForm = document.querySelector("#smart-project-form");
const smartNotesInput = document.querySelector("#smart-notes");
const smartProjectMessage = document.querySelector("#smart-project-message");

function updateProjects() {
    const query = filterInput.value.trim().toLowerCase();
    const projectCards = Array.from(projectsGrid.querySelectorAll(".card"));
    let visibleCount = 0;
    const visibleProjectTitles = [];

    projectCards.forEach((card) => {
        const matches = card.textContent.toLowerCase().includes(query);
        card.classList.toggle("hidden", !matches);
        if (matches) {
            visibleCount += 1;
            visibleProjectTitles.push(card.querySelector("h3").textContent.trim());
        }
    });

    projectCount.textContent = `Showing ${visibleCount} of ${projectCards.length} projects`;
    console.log(visibleProjectTitles);
}

function updateTrendingBadge(card, likes) {
    const badge = card.querySelector(".trending-badge");
    if (likes > 10 && !badge) {
        const newBadge = document.createElement("span");
        newBadge.className = "trending-badge";
        newBadge.textContent = "Trending";
        card.querySelector("h3").after(newBadge);
    } else if (likes <= 10 && badge) {
        badge.remove();
    }
}

function createProjectCard(project) {
    const card = document.createElement("article");
    card.className = "card";
    card.dataset.projectId = project.id;

    const title = document.createElement("h3");
    title.textContent = project.title;
    card.append(title);

    if (project.likes > 10) {
        const badge = document.createElement("span");
        badge.className = "trending-badge";
        badge.textContent = "Trending";
        card.append(badge);
    }

    const author = document.createElement("p");
    author.textContent = `Author: ${project.author_name}`;
    card.append(author);

    const description = document.createElement("p");
    description.textContent = project.summary || project.description;
    card.append(description);

    if (Array.isArray(project.technologies) && project.technologies.length > 0) {
        const technologies = document.createElement("p");
        technologies.textContent = `Technologies: ${project.technologies.join(", ")}`;
        card.append(technologies);
    }

    const likeLine = document.createElement("p");
    likeLine.append("Likes: ");
    const likeCount = document.createElement("span");
    likeCount.className = "like-count";
    likeCount.textContent = project.likes;
    likeLine.append(likeCount);
    card.append(likeLine);

    const upvoteButton = document.createElement("button");
    upvoteButton.className = "upvote-btn button";
    upvoteButton.type = "button";
    upvoteButton.textContent = "Upvote";
    card.append(upvoteButton);

    return card;
}

filterInput.addEventListener("input", updateProjects);
updateProjects();

projectsGrid.addEventListener("click", async (event) => {
    const upvoteButton = event.target.closest(".upvote-btn");
    if (!upvoteButton || !projectsGrid.contains(upvoteButton)) {
        return;
    }

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
        updateTrendingBadge(card, result.likes);
    } catch (error) {
        console.error("Unable to upvote project:", error);
    } finally {
        upvoteButton.disabled = false;
    }
});

newProjectForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    createProjectMessage.textContent = "";

    try {
        const response = await fetch("/api/projects", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ title: newTitleInput.value }),
        });
        if (!response.ok) {
            createProjectMessage.textContent = "Unable to add project. Enter a title and try again.";
            return;
        }

        const project = await response.json();
        projectsGrid.append(createProjectCard(project));
        newTitleInput.value = "";
        updateProjects();
    } catch (error) {
        createProjectMessage.textContent = "Unable to add project. Please try again.";
        console.error("Unable to create project:", error);
    }
});

smartProjectForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    smartProjectMessage.textContent = "";

    if (smartNotesInput.value.trim().length < 20) {
        smartProjectMessage.textContent = "Please enter at least 20 characters of notes.";
        return;
    }

    const smartButton = smartProjectForm.querySelector("button");
    smartButton.disabled = true;
    try {
        const response = await fetch("/api/projects/smart", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ notes: smartNotesInput.value }),
        });
        if (!response.ok) {
            const result = await response.json();
            smartProjectMessage.textContent = result.error || "Unable to create project.";
            return;
        }

        const project = await response.json();
        projectsGrid.append(createProjectCard(project));
        smartNotesInput.value = "";
        smartProjectMessage.textContent = "Project created.";
        updateProjects();
    } catch (error) {
        smartProjectMessage.textContent = "Unable to create project. Please try again.";
        console.error("Unable to smart create project:", error);
    } finally {
        smartButton.disabled = false;
    }
});
