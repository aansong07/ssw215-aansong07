# SPEC: Developer Portfolio Welcome Page
## 1. Purpose & Scope
- A personal portfolio welcome page for <Akosua Ansong>, a first-year software
engineering student.
- Non-Goals: no multi-page routing; no backend; no contact forms.
## 2. Invariants & Negative Constraints
- All styling MUST reside in `./style.css` (no inline style="..." attributes).
- The page MUST NOT load external CSS frameworks or CDNs (no Bootstrap, no Tailwind).
- The avatar image MUST use the relative path `./assets/avatar.jpg`.
- The layout MUST collapse into a single vertical column on screens narrower than 768px.
## 3. UI Content & Interface Contract
- Hero header: my full name "<Akosua Ansong>", the subtitle "<I live in Hillside NJ>", and
this bio: "<I like to watch movies and listen to music. I also recently started going to the gym.>".
- Action link: a button labelled "See my projects" that links to `#projects`.
- Projects section with id="projects": lists these items: <I have made a blackjack simulator in java. I want to make a gym workout planner, and something related to music.>.
- Social link: GitHub (https://github.com/aansong07) MUST open in a new tab
(target="_blank").
## 4. Acceptance Checklist
- [ ] Valid semantic HTML5: the page uses <header>, <main>, and <footer>.
- [ ] The avatar image has width, height, and alt attributes.
- [ ] No horizontal scrollbar when the browser is narrowed to 375px.
- [ ] The GitHub link opens in a new tab and has rel="noopener".
- [ ] No placeholder links: href="#" appears nowhere.
## 5. Audit Protocol
- Inspect the generated code line by line with `git diff --staged` before committing.