document.getElementById('fetchBtnmnt').addEventListener('click', fetchData);

async function fetchData() {
  const outputDiv = document.getElementById('mnt');
  outputDiv.textContent = "Fetching...";

  const d = new Date();

  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = String(d.getFullYear()).slice(-2);

  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  const seconds = String(d.getSeconds()).padStart(2, "0");

  const dt = `${year}-${month}-${day}`;	
  const tm = `${hours}:${minutes}:${seconds}`;

  try {
    // 1. Hit the Endpoint
    const response = await fetch('https://in.adda.io/actions/ajax_maintenance_trackfees_table.php?income_filter=4&choosen_block=All%20Blocks&shouldSearch=0&show_advance_allocations=-1&now=%22{dt}%20{tm}%22&empty=1');

    // 2. Get text (HTML string)
    const htmlText = await response.text();

    //console.log(htmlText);

    // 2. Parse the HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, 'text/html');

    // 3. Select the rows inside the table body
    // We target 'tbody tr' to skip the header row
    const rows = doc.querySelectorAll('table tbody tr'); 

    let results = [];

    // 4. Iterate and Filter
    rows.forEach((row) => {
      const cells = row.querySelectorAll('td');

      // Make sure the row has enough columns (Your table has ~11 cols)
      if (cells.length > 6) {
        
        // Extract raw text
        const block = cells[3].innerText.trim().replace('Utility ',''); // Column 4
        const unit = cells[4].innerText.trim();  // Column 5
        const dueText = cells[6].innerText.trim(); // Column 7 ("8,246.00")

        // Clean the Due Amount: Remove commas to parse as number
        // "8,246.00" -> "8246.00" -> 8246.00
        const dueAmount = parseFloat(dueText.replace(/,/g, ''));

        // Filter Logic: Check if valid number and not equal to 0
        if (!isNaN(dueAmount) && dueAmount > 0) {
          results.push(`${block}${unit}`);
        }
      }
    });

	
const result = [];
const seen = new Set();

results.forEach(code => {
  // Skip invalid entries
  if (typeof code !== "string") return;

  const value = code.trim();
  if (!value) return;

  // Skip existing Block-* entries
  if (value.startsWith("Block")) return;

  const block = value[0];

  // Ensure block is a letter
  if (!/[A-Z]/i.test(block)) return;

  if (!seen.has(block)) {
    seen.add(block);
    result.push("",`*Block-${block}*`);
  }

  result.push(value);
});
	
    // 5. Display Output
    if (results.length > 0) {
      outputDiv.textContent = "Dear Residents,\n\nMaintenance for this quarter is still pending for the following units." + "Kindly clear the dues at the earliest: \n" + result.join('\n');
    } else {
      outputDiv.textContent = "No dues found (or parse error).";
    }

  } catch (error) {
    console.error(error);
    outputDiv.textContent = "Error: " + error.message;
  }
}