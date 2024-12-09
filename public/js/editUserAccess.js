const editUserForm = document.getElementById("edit-user-access-form");

function submitForm(event) {
  event.preventDefault();

  const data = new FormData(editUserForm);
  const payload = {};

  for (const entry of data.entries()) {
    payload[entry[0]] = entry[1];
  }

  payload["access_level"] = parseInt(payload["access_level"]);

  const path = `/api/users/${payload["user_id"]}/access`;
  const method = "PATCH";

  delete payload["user_id"];

  fetch(path, {
    method,
    body: JSON.stringify(payload),
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then(async (res) => {
      const data = await res.json();
      if (res.status == 200) {
        alert(data.message);
      } else {
        alert(data.detail);
      }
    })
    .catch((err) => {
      alert(err);
    });
}

editUserForm.addEventListener("submit", submitForm);
