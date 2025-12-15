const DATA = JSON.parse(
  document.getElementById("data-json").textContent
);

const state = {
  top: 0,
  bottom: 0,
  shoes: 0
};

function update(type) {
  const list = DATA[type];
  const img = document.getElementById(type + "-img");

  if (!list || list.length === 0) {
    img.style.display = "none";
    return;
  }

  const item = list[state[type]];
  if (!item.image_filename) {
    img.style.display = "none";
    return;
  }

  img.style.display = "block";
  img.src = `/static/uploads/processed/${item.image_filename}`;
}

document.querySelectorAll(".arrow").forEach(btn => {
  const type = btn.dataset.type;

  btn.onclick = () => {
    if (!DATA[type] || DATA[type].length === 0) return;

    state[type] =
      btn.classList.contains("left")
        ? (state[type] - 1 + DATA[type].length) % DATA[type].length
        : (state[type] + 1) % DATA[type].length;

    update(type);
  };
});
let selectedOuterwear = null;
let selectedAccessory = null;

// OUTERWEAR
document.querySelectorAll(".outerwear-item").forEach(el => {
  el.onclick = () => {
    document
      .querySelectorAll(".outerwear-item")
      .forEach(i => i.classList.remove("active"));

    el.classList.add("active");
    selectedOuterwear = el.dataset.id;
  };
});

// ACCESSORIES
document.querySelectorAll(".accessory-item").forEach(el => {
  el.onclick = () => {
    document
      .querySelectorAll(".accessory-item")
      .forEach(i => i.classList.remove("active"));

    el.classList.add("active");
    selectedAccessory = el.dataset.id;
  };
});
["top", "bottom", "shoes"].forEach(update);
