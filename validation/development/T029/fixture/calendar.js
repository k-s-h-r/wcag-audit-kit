const message = document.querySelector('#message');
const confirmation = document.querySelector('#confirmation');
for (const button of document.querySelectorAll('.day')) {
  button.addEventListener('click', () => {
    const date = `5月${button.dataset.day}日`;
    if (button.classList.contains('available')) {
      message.textContent = `${date}には空きがあります。`;
      confirmation.href = `confirmation.html?day=${encodeURIComponent(button.dataset.day)}`;
      confirmation.hidden = false;
    } else {
      message.textContent = `${date}は満席です。別の日を選んでください。`;
      confirmation.hidden = true;
    }
  });
}
