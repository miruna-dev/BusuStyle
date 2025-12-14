document.addEventListener("DOMContentLoaded", () => {

  const sections = [
    {
      title: "Create outfit collages",
      desc: "Combină hainele tale pe un canvas și creează outfit-uri unice.",
      phone: "Canvas outfits"
    },
    {
      title: "Your personal dressing room",
      desc: "Vezi toate hainele tale într-un singur loc și construiește outfit-uri rapid.",
      phone: "Closet view"
    },
    {
      title: "Realistic virtual try on",
      desc: "Testează combinații înainte să le porți sau să le cumperi.",
      phone: "Try on preview"
    }
  ];

  const titleEl = document.getElementById("magic-title");
  const descEl = document.getElementById("magic-desc");
  const phoneEl = document.getElementById("magic-phone-content");
  const scrollSection = document.querySelector(".scroll-magic");

  if (!titleEl || !descEl || !phoneEl || !scrollSection) {
    console.warn("Scroll magic elements missing");
    return;
  }

  function updateContent(index) {
    titleEl.textContent = sections[index].title;
    descEl.textContent = sections[index].desc;
    phoneEl.textContent = sections[index].phone;
  }

  updateContent(0);

  window.addEventListener("scroll", () => {
    const rect = scrollSection.getBoundingClientRect();
    const maxScroll = scrollSection.offsetHeight - window.innerHeight;

    if (maxScroll <= 0) return;

    const progress = Math.min(
      Math.max(-rect.top / maxScroll, 0),
      1
    );

    const index = Math.floor(progress * sections.length);
    updateContent(Math.min(index, sections.length - 1));
  });

});
