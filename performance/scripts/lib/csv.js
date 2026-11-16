// RFC4180-style quoted fields, escaped quotes, CRLF and UTF-8 BOM; no remote parser.
export function parseCSV(text) {
  text = text.replace(/^\uFEFF/, '');
  const rows = [];
  let row = [], field = '', quoted = false, closed = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') { quoted = false; closed = true; }
      else field += c;
    } else if (c === '"') {
      if (field || closed) throw new Error('Malformed CSV quote');
      quoted = true;
    } else if (c === ',' || c === '\n' || c === '\r') {
      row.push(field); field = ''; closed = false;
      if (c !== ',') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        if (row.some(v => v !== '')) rows.push(row);
        row = [];
      }
    } else {
      if (closed) throw new Error('Unexpected text after CSV quote');
      field += c;
    }
  }
  if (quoted) throw new Error('Unterminated CSV quote');
  if (field || closed || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift();
  const expected = ['email', 'password', 'keyword', 'productId', 'quantity', 'shippingAddress'];
  if (!headers || headers.join(',') !== expected.join(',')) throw new Error('CSV header mismatch');
  const emails = new Set();
  return rows.map((cells, index) => {
    if (cells.length !== headers.length) throw new Error(`CSV column count at row ${index + 2}`);
    const item = Object.fromEntries(headers.map((h, i) => [h, cells[i]]));
    if (cells.some(v => !v.trim()) || emails.has(item.email)) throw new Error(`Empty/duplicate CSV row ${index + 2}`);
    emails.add(item.email);
    for (const key of ['productId', 'quantity']) {
      item[key] = Number(item[key]);
      if (!Number.isSafeInteger(item[key]) || item[key] <= 0) throw new Error(`Invalid ${key}`);
    }
    return item;
  });
}
