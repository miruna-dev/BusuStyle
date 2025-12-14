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

document.querySelectorAll(".carousel").forEach(c => {
  const type = c.dataset.type;
  if (!type) return;

  c.querySelector(".left").onclick = () => {
    state[type] =
      (state[type] - 1 + DATA[type].length) % DATA[type].length;
    update(type);
  };

  c.querySelector(".right").onclick = () => {
    state[type] =
      (state[type] + 1) % DATA[type].length;
    update(type);
  };

  update(type);
});

document.querySelectorAll(".list img, .placeholder").forEach(el => {
  el.onclick = () => {
    el.parentElement
      .querySelectorAll(".active")
      .forEach(x => x.classList.remove("active"));
    el.classList.add("active");
  };
});
