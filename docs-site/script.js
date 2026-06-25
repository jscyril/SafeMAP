const sidebar = document.querySelector("#sidebar");
const toggle = document.querySelector(".nav-toggle");
const links = [...document.querySelectorAll(".nav a")];
const search = document.querySelector("#doc-search");
const chapters = [...document.querySelectorAll(".chapter[id]")];

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
