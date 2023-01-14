// Handle checkboxes in tables, and modal forms
'use strict';
var tableFunctions = (function () {
  let tb = {};
  let lastChecked = null;

  tb.init = function () {
    document.getElementById('select_all_page').addEventListener("click", selectAllPage);
    document.getElementById('select_all').addEventListener("click", selectAll);
    Array.from(document.getElementsByTagName("table")).forEach(e => e.addEventListener("click", tableClick));
  }

  function selectAllPage() {
    // Click on 'Select all on page' highlights all rows
    document.getElementById('select_all').checked = false;
    let checked = this.checked;
    Array.from(document.getElementsByClassName("select-checkbox")).forEach(function (box) {
      box.checked = checked;
      box.disabled = false;
      highlightRow(box);
    })
    countChecked();
    lastChecked = null;
  }

  function selectAll() {
    // Click on Select all highlights all rows and disables checkboxes
    document.getElementById('select_all_page').checked = false;
    let checked = this.checked;
    Array.from(document.getElementsByClassName("select-checkbox")).forEach(function (box) {
      box.checked = checked;
      box.disabled = checked;
      highlightRow(box);
    })
    if (checked) {
      document.getElementById('count').innerText = 'All';
    } else {
      document.getElementById('count').innerText = '0';
    }
    document.getElementById('selectActionMenu').disabled = !checked;
    lastChecked = null;
  }

  function tableClick(e) {
    if (e.target.name === 'select-checkbox') {
      // Click on row's select checkbox - handle using shift to select multiple rows
      let chkBox = e.target;
      highlightRow(chkBox);
      if (!lastChecked) {
        lastChecked = chkBox;
      } else if (e.shiftKey) {
        let start = chkBoxes.indexOf(chkBox);
        let end = chkBoxes.indexOf(lastChecked);
        Array.from(document.getElementsByClassName("select-checkbox")).slice(Math.min(start, end), Math.max(start, end) + 1).forEach(function (box) {
          box.checked = chkBox.checked;
          highlightRow(box)
        });
        lastChecked = chkBox;
      } else {
        lastChecked = chkBox;
      }
      countChecked();

    } else if (e.target.tagName === 'TD') {
      // Click on cell causes redirect if href is defined in parent row
      if ("href" in e.target.parentNode.dataset) {
        window.document.location = e.target.parentNode.dataset.href
      } else if ("modal" in e.target.parentNode.dataset) {
        let target = e.target.parentNode.dataset.modal;
        if (target === '') {
          target = '#modals-here';
        } else {
          target = '#' + target;
        }
        // Click on cell causes htmx GET
        htmx.ajax('GET', '', {source: '#' + e.target.parentNode.id, target: target})
      }
    }
  }

  function highlightRow(box) {
    let row = box.parentElement.parentElement;
    let cls = (("selected" in row.dataset) ? row.dataset.selected : "table-active");
    if (box.checked) {
      row.classList.add(cls)
    } else {
      row.classList.remove(cls)
    }
  }

// Count the number of checked rows
  function countChecked() {
    let count = document.querySelectorAll('.select-checkbox:checked').length;
    document.getElementById('count').innerText = count.toString();
    document.getElementById('selectActionMenu').disabled = (count === 0)
  }

  return tb
})();



