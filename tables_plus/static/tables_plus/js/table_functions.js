// Handle checkboxes in tables, and modal forms
'use strict';
var tableFunctions = (function () {
    let tb = {};
    let lastChecked = null;

    tb.init = function () {
      let selAll = document.getElementById('select_all')
      if (selAll) {
        selAll.addEventListener("click", selectAll)
      }
      let selAllPage = document.getElementById('select_all_page')
      if (selAllPage) {
        selAllPage.addEventListener("click", selectAllPage)
      }
      Array.from(document.getElementsByTagName("table")).forEach(e => e.addEventListener("click", tableClick));
      Array.from(document.querySelectorAll(".auto-submit")).forEach(e => e.addEventListener("change", function () {
        document.getElementById("id_table_form").submit()
      }));
      Array.from(document.querySelectorAll(".form-group.hx-get")).forEach(e => e.addEventListener("change", filterChanged));
      countChecked()
      document.body.addEventListener("trigger", function (evt) {
        htmx.ajax('GET', evt.detail.url, {source: '#table_data', 'target': '#table_data'});
      })
      if (window.matchMedia("(max-width: 768px)").matches) {
        setMobileTable("table")
      }
    }

    function filterChanged() {
      htmx.ajax('GET', '', {source: '#' + this.lastChild.id, target: '#table_data'});
    }

    function checkBoxes() {
      return Array.from(document.getElementsByClassName("select-checkbox"))
    }

    function selectAllPage() {
      // Click on 'Select all on page' highlights all rows
      let checked = this.checked;
      if (checked) {
        document.getElementById('select_all').parentElement.style.display='block';
      } else {
        document.getElementById('select_all').parentElement.style.display='none';
      }
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
      let checked = this.checked;
      if (checked) {
        document.getElementById('count').innerText = 'All';
      } else {
        document.getElementById('select_all_page').disabled = false;
        Array.from(document.getElementsByClassName("select-checkbox")).forEach(function (box) {
          box.checked = true;
          box.disabled = false;
          highlightRow(box);
          countChecked();
        })
      }
      lastChecked = null;
    }

    function tableClick(e) {
      if (e.target.name === 'select-checkbox') {
        // Click on row's select checkbox - handle using shift to select multiple rows
        document.getElementById('select_all_page').checked = false;
        document.getElementById('select_all').parentElement.style.display='none';
        let chkBox = e.target;
        highlightRow(chkBox);
        if (!lastChecked) {
          lastChecked = chkBox;
        } else if (e.shiftKey) {
          let chkBoxes = checkBoxes();
          let start = chkBoxes.indexOf(chkBox);
          let end = chkBoxes.indexOf(lastChecked);
          chkBoxes.slice(Math.min(start, end), Math.max(start, end) + 1).forEach(function (box) {
            box.checked = chkBox.checked;
            // highlightRow(box)
          });
          lastChecked = chkBox;
        } else {
          lastChecked = chkBox;
        }
        countChecked();

      } else if (e.target.tagName === 'TD') {
        let editing = document.getElementById("editing");
        if (editing) {
          htmx.ajax('POST', "", {source: '#' + editing.id, target: '#' + editing.id})
        } else {
          let row = e.target.parentNode;
          let table = row.parentNode.parentNode;
          let col = 0;
          let previous = e.target.previousElementSibling;
          while (previous) {
            previous = previous.previousElementSibling;
            col += 1;
          }
          let id = row.id.slice(3);
          if (table.dataset.url) {
            let url = table.dataset.url;
            if (table.dataset.pk) {
              url += id;
            }
            if (table.dataset.method === "get") {
              window.document.location = url;
            } else if (table.dataset.method === "hxget") {
              htmx.ajax('GET', url, {source: '#' + row.id, target: table.dataset.target});
            }
          } else if (e.target.classList.contains("td_edit")) {
            let tdId = ("td" + "_" + id + "_" + col);
            e.target.setAttribute("id", tdId);
            htmx.ajax('GET', "", {source: '#' + tdId, target: '#' + tdId});
          }
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

// Count the number of checked rows and nake sure they are highlighted
    function countChecked() {
      let checked = Array.from(document.querySelectorAll(".select-checkbox:checked"));
      checked.forEach(function (e) {
        let row = e.parentElement.parentElement
        row.classList.add((("selected" in row.dataset) ? row.dataset.selected : "table-active"))
      });
      let count = checked.length;
      let countField = document.getElementById('count');
      countField.innerText = count.toString();
      let actionMenu = document.getElementById('selectActionMenu');
      if (actionMenu) {
        actionMenu.disabled = (count === 0);
      }
    }

    function setMobileTable(selector) {
      // if (window.innerWidth > 600) return false;
      const tableEl = document.querySelector(selector);
      const thEls = tableEl.querySelectorAll('thead th');
      const tdLabels = Array.from(thEls).map(el => el.innerText);
      tableEl.querySelectorAll('tbody tr').forEach(tr => {
        Array.from(tr.children).forEach(
          (td, ndx) => td.setAttribute('label', tdLabels[ndx])
        );
      });
    }

    return tb
  }

)
();



