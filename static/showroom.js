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

document.querySelectorAll(".outerwear-item").forEach(el => {
  el.onclick = () => {
    if (el.classList.contains("active")) {
      el.classList.remove("active");
      selectedOuterwear = null;
      return;
    }

    document
      .querySelectorAll(".outerwear-item")
      .forEach(i => i.classList.remove("active"));

    el.classList.add("active");
    selectedOuterwear = el.dataset.id;
  };
});


document.querySelectorAll(".accessory-item").forEach(el => {
  el.onclick = () => {
    if (el.classList.contains("active")) {
      el.classList.remove("active");
      selectedAccessory = null;
      return;
    }

    document
      .querySelectorAll(".accessory-item")
      .forEach(i => i.classList.remove("active"));

    el.classList.add("active");
    selectedAccessory = el.dataset.id;
  };
});

function syncHiddenInputs() {
  const topItem = DATA.top[state.top];
  const bottomItem = DATA.bottom[state.bottom];
  const shoesItem = DATA.shoes[state.shoes];

  document.getElementById("top-id").value = topItem ? topItem.id : "";
  document.getElementById("bottom-id").value = bottomItem ? bottomItem.id : "";
  document.getElementById("shoes-id").value = shoesItem ? shoesItem.id : "";

  document.getElementById("outerwear-id").value = selectedOuterwear || "";
  document.getElementById("accessories-id").value = selectedAccessory || "";
}

const form = document.getElementById("save-outfit-form");

form.addEventListener("submit", e => {
  syncHiddenInputs();
});




["top", "bottom", "shoes"].forEach(update);
