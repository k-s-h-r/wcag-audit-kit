const query = new URLSearchParams(location.search);
const dates = { '2026-12-20': '12月20日' };
const date = dates[query.get('date')] ?? '日付未指定';
const people = query.get('people') ?? '未指定';
document.getElementById('summary').textContent = `${date}。見学人数 ${people} 名。`;
