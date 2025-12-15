document.addEventListener("DOMContentLoaded", () => {

  const sections = [
    {
      title: "Create outfit collages",
      desc: "Combină hainele aici până îți iese o ținută de Oscar. Sau până te enervezi și iei tot hanoracul ăla negru.",
      image: "/static/uploads/busufainosag.png"
    },
    {
      title: "Your personal dressing room",
      desc: "Te aranjăm noi",
      image: "/static/uploads/netiiubita.png"
    },
    {
      title: "Realistic virtual try on",
      desc: "Vezi cum îți stă cu ele fără să te dezbraci.",
      image: "/static/uploads/barbiepreview.png"
    }
  ];

  const titleEl = document.getElementById("magic-title");
  const descEl = document.getElementById("magic-desc");
  const phoneEl = document.getElementById("magic-phone-content");
  const scrollSection = document.querySelector(".scroll-magic");

  if (!titleEl || !descEl || !phoneEl || !scrollSection) {
    return;
  }

  const imgEl = document.getElementById("magic-phone-img");

  function updateContent(index) {
    titleEl.textContent = sections[index].title;
    descEl.textContent = sections[index].desc;
    imgEl.src = sections[index].image;
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
