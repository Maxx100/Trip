function formatDateTime(unixTs) {
  const date = new Date(unixTs * 1000);
  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(date);
}

function renderRows(tableId, rows) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  if (!tbody) return;

  tbody.innerHTML = '';

  rows.forEach((row) => {
    const [name, eur, usd] = row;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${name}</td>
      <td>${eur.toFixed(2)}</td>
      <td>${usd.toFixed(2)}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadCurrencyRates() {
  const errorBox = document.getElementById('currencyError');
  const updatedAt = document.getElementById('currencyUpdatedAt');
  const currencyGrid = document.querySelector('.currency-grid');

  try {
    const response = await fetch('/api/currency-rate', {
      method: 'GET',
      headers: { Accept: 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    const rates = payload?.rates || {};
    const today = rates.today || [];
    const tomorrow = rates.tomorrow || [];

    renderRows('currencyTodayTable', today);
    renderRows('currencyTomorrowTable', tomorrow);

    if (currencyGrid) {
      currencyGrid.style.display = 'grid';
    }
    if (errorBox) {
      errorBox.hidden = true;
      errorBox.textContent = '';
    }

    if (updatedAt) {
      updatedAt.textContent = `Обновлено: ${formatDateTime(payload.updated_at)} (${payload.source === 'cache' ? 'кэш' : 'актуальные данные'})`;
    }
  } catch (error) {
    if (currencyGrid) {
      currencyGrid.style.display = 'none';
    }
    if (errorBox) {
      errorBox.hidden = false;
      errorBox.textContent = 'Не удалось загрузить курсы валют. Попробуйте обновить страницу позже.';
    }
    if (updatedAt) {
      updatedAt.textContent = '';
    }
  }
}

loadCurrencyRates();
