let enabled = false;
const control = document.querySelector('#email-switch');
control.addEventListener('click', () => {
  enabled = !enabled;
  document.querySelector('#visual-state').textContent = enabled ? 'On' : 'Off';
  if (document.querySelector('main').dataset.stateExposure === 'correct') {
    control.setAttribute('aria-checked', String(enabled));
  }
});
