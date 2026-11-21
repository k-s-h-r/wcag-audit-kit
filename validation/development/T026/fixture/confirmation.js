const value = new URLSearchParams(location.search).get('people');
document.getElementById('summary').textContent = `12月6日。見学人数 ${value ?? '未指定'} 名。`;
