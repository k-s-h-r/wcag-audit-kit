'use strict';

const days = [
  { date: '12月14日', available: false },
  { date: '12月15日', available: false },
  { date: '12月16日', available: false },
  { date: '12月17日', available: false },
  { date: '12月18日', available: false },
  { date: '12月19日', available: true },
  { date: '12月20日', available: true },
];
let current = 0;
const availability = document.querySelector('#availability');
const nextDay = document.querySelector('#next-day');
const nextAvailable = document.querySelector('#next-available');

function showDay(index) {
  current = index;
  const day = days[current];
  availability.textContent = day.date + '、' + (day.available ? '空きあり。' : '空きなし。');
  nextDay.setAttribute('aria-disabled', String(current === days.length - 1));
  if (nextAvailable) {
    nextAvailable.setAttribute('aria-disabled', String(!days.slice(current + 1).some(day => day.available)));
  }
}

nextDay.addEventListener('click', () => {
  if (current < days.length - 1) showDay(current + 1);
});
nextAvailable?.addEventListener('click', () => {
  const next = days.findIndex((day, index) => index > current && day.available);
  if (next !== -1) showDay(next);
});
