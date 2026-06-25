const sidebar = document.querySelector("#sidebar");
const toggle = document.querySelector(".nav-toggle");
const themeToggle = document.querySelector(".theme-toggle");
const themeLabel = document.querySelector(".theme-label");
const themeIcon = document.querySelector(".theme-icon");
const links = [...document.querySelectorAll(".nav a")];
const search = document.querySelector("#doc-search");
const chapters = [...document.querySelectorAll(".chapter[id]")];

const storedTheme = localStorage.getItem("safemap-docs-theme");
if (storedTheme === "dark" || storedTheme === "light") {
  document.documentElement.dataset.theme = storedTheme;
}

function currentTheme() {
  const explicit = document.documentElement.dataset.theme;
  if (explicit) {
    return explicit;
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function syncThemeButton() {
  const theme = currentTheme();
  const isDark = theme === "dark";
  themeToggle?.setAttribute("aria-pressed", String(isDark));
  if (themeLabel) {
    themeLabel.textContent = isDark ? "Light" : "Dark";
  }
  if (themeIcon) {
    themeIcon.textContent = isDark ? "☼" : "◐";
  }
}

themeToggle?.addEventListener("click", () => {
  const next = currentTheme() === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem("safemap-docs-theme", next);
  syncThemeButton();
});

window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  if (!localStorage.getItem("safemap-docs-theme")) {
    syncThemeButton();
  }
});

syncThemeButton();

toggle?.addEventListener("click", () => {
  const isOpen = sidebar.classList.toggle("open");
  toggle.setAttribute("aria-expanded", String(isOpen));
});

links.forEach((link) => {
  link.addEventListener("click", () => {
    sidebar.classList.remove("open");
    toggle?.setAttribute("aria-expanded", "false");
  });
});

search?.addEventListener("input", () => {
  const query = search.value.trim().toLowerCase();
  links.forEach((link) => {
    const text = link.textContent.toLowerCase();
    link.classList.toggle("hidden", query.length > 0 && !text.includes(query));
  });
});

const observer = new IntersectionObserver(
  (entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) {
      return;
    }
    links.forEach((link) => {
      link.classList.toggle("active", link.getAttribute("href") === `#${visible.target.id}`);
    });
  },
  {
    rootMargin: "-20% 0px -60% 0px",
    threshold: [0.1, 0.25, 0.5],
  },
);

chapters.forEach((chapter) => observer.observe(chapter));
