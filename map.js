// # Global

let categories = [];
let establishments = [];
const filters = {
  search: "",
  categories: [],
  cuisines: [],
  status: "all",
};

// # Leaflet
// ## Map

const NYC = [40.7128, -74.006];

const map = L.map("map", { zoomControl: false })
  .setView(NYC, 11)
  .setMaxBounds(
    L.latLngBounds([
      [40.976, -74.398],
      [40.413, -73.591],
    ]),
  )
  .setMinZoom(11);

L.control.zoom({ position: "bottomright" }).addTo(map);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);

// ## Icons

const icons = new Map();

function escapeHTML(s) {
  if (s == null) return "";
  return String(s).replace(
    /[&<>"']/g,
    (c) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[c],
  );
}

function popupRow(title, value) {
  if (value)
    return `<div class="p-row"><strong>${title}:</strong> ${value}</div>`;
  else return "";
}

function urlHTML(url) {
  try {
    if (url.includes("instagram")) {
      const name = `@${url.replace(/^.*\.com\//, "").split("/")[0]}`;
      return `<a href="${encodeURI(url)}" target="_blank" rel="noopener noreferrer">${name}</a>`;
    } else {
      const name = new URL(url).hostname.replace(/^www\./, "");
      return `<a href="${encodeURI(url)}" target="_blank" rel="noopener noreferrer">${name}</a>`;
    }
  } catch {
    return url;
  }
}

function popup(establishment) {
  return `
  <div class="popup">
    <h3>${establishment.name}</h3>
    <div class="popup-meta">
      ${escapeHTML(establishment.category)} ${establishment.cuisine ? ` · ${escapeHTML(establishment.cuisine)}` : ""}
    </div>
    <div class="popup-row">
      ${popupRow("Address", escapeHTML(establishment.full_address))}
      ${popupRow("Phone", escapeHTML(establishment.phone_number))}
      ${popupRow("Website", urlHTML(establishment.website))}
    </div>
  </div>
  `;
}

function establishmentFilter(establishment) {
  if (
    filters.categories.length !== 0 &&
    !filters.categories.includes(establishment.category)
  )
    return false;

  if (
    filters.cuisines.length !== 0 &&
    !filters.cuisines.includes(establishment.cuisine)
  )
    return false;

  if (
    filters.status === "wouldNotReturn" &&
    !(establishment.have_been && !establishment.would_return)
  )
    return false;
  if (
    filters.status === "wouldReturn" &&
    !(establishment.have_been && establishment.would_return)
  )
    return false;
  if (filters.status === "unvisited" && establishment.have_been) return false;

  if (filters.search) {
    const haystack = [
      establishment.name,
      establishment.cuisine,
      establishment.category,
      establishment.full_address,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    if (!haystack.includes(filters.search)) return false;
  }

  return true;
}

function select(id, pan) {
  document
    .querySelectorAll(".establishments li")
    .forEach((item) =>
      item.classList.toggle("is-active", item.dataset.id == id),
    );

  const icon = icons.get(id);
  if (pan) {
    map.setView(icon.getLatLng(), Math.max(map.getZoom(), 15), {
      animate: true,
    });
  }
  icon.openPopup();
  const item = document.querySelector(`.establishments li[data-id="${id}"]`);
  item.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

function displayList(establishments) {
  const establishmentsList = document.getElementById("establishments");
  establishmentsList.innerHTML = "";

  const fragment = document.createDocumentFragment();
  establishments.forEach((establishment) => {
    const item = document.createElement("li");
    item.dataset.id = establishment.id;

    item.innerHTML = `
    <div>${escapeHTML(establishment.name)}</div>
    <div>
    </div>
      <span>${escapeHTML(establishment.category)}</span>
      ${establishment.cuisine ? `<span class="dot">·</span><span>${escapeHTML(establishment.cuisine)}</span>` : ""}
    <div>
    </div>
    <div class="establishment-address">${establishment.full_address}</div>
    `;
    item.addEventListener("click", () => select(establishment.id, true));
    fragment.appendChild(item);
  });

  establishmentsList.appendChild(fragment);
}

function show() {
  icons.forEach((icon) => icon.remove());
  icons.clear();

  const establishmentsFiltered = establishments.filter(establishmentFilter);

  establishmentsFiltered.forEach((establishment) => {
    const icon = L.marker([establishment.latitude, establishment.longitude])
      .bindPopup(popup(establishment), { maxWidth: 300 })
      .addTo(map);

    icon.on("click", () => select(establishment.id, false));
    icons.set(establishment.id, icon);
  });

  // displayList(
  //   establishmentsFiltered.toSorted((a, b) => a.name.localeCompare(b.name)),
  // );
}

// # Document

function populateDropdown(id, items) {
  const element = document.getElementById(id);
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[id];
    option.textContent = item[id];
    element.append(option);
  });
}

// ## Event Listeners

document.getElementById("search").addEventListener("input", (event) => {
  filters.search = event.target.value.trim().toLowerCase();
  show();
});

document.getElementById("category").addEventListener("change", (event) => {
  filters.categories = [];
  if (event.target.value != "") filters.categories.push(event.target.value);
  show();
});

document.getElementById("cuisine").addEventListener("change", (event) => {
  filters.cuisines = [];
  if (event.target.value != "") filters.cuisines.push(event.target.value);
  show();
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".chip[disabled]").forEach((chip) => {
      chip.disabled = false;
    });
    chip.disabled = true;
    filters.status = chip.dataset.status;
    show();
  });
});

// # Data

function rows(result) {
  if (!result.length) return [];
  const { columns, values } = result[0];
  return values.map((value) =>
    Object.fromEntries(columns.map((column, i) => [column, value[i]])),
  );
}

async function load() {
  const sql = await initSqlJs({
    locateFile: (file) =>
      `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/${file}`,
  });

  const dbFile = await fetch("./data/establishments.db");
  if (!dbFile.ok) throw new Error(`Faild to fetch data: ${dbFile.status}`);

  const buffer = await dbFile.arrayBuffer();
  const db = new sql.Database(new Uint8Array(buffer));

  establishments = rows(
    db.exec(`
      SELECT
        id,
        name,
        website,
        phone_number,
        full_address,
        latitude,
        longitude,
        category,
        cuisine,
        have_been,
        would_return,
        closed
      FROM
        greater_ny LEFT JOIN v_full_address USING (id)
      WHERE
        closed = FALSE;
    `),
  );

  // TODO: make sure that categories / cuisines are consistent with what are shown

  const categories = rows(
    db.exec("SELECT DISTINCT category FROM greater_ny ORDER BY category"),
  );
  populateDropdown("category", categories);

  const cuisines = rows(
    db.exec("SELECT DISTINCT cuisine FROM greater_ny ORDER BY cuisine"),
  );
  populateDropdown("cuisine", cuisines);

  show();
}

// # Main

load();
