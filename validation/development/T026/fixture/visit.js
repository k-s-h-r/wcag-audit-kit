const form = document.getElementById('reservation');
const people = document.getElementById('people');
const error = document.getElementById('error');

form.addEventListener('submit', (event) => {
  if (!/^\d+$/.test(people.value) || Number(people.value) < 2) {
    event.preventDefault();
    people.setAttribute('aria-invalid', 'true');
    error.textContent = '見学人数は2名以上を入力してください。';
  }
});
