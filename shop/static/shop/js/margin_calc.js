function margin_calc() {
  let cost = value_or_zero("id_cost_price");
  let restoration = value_or_zero("id_restoration_cost");
  let sale = value_or_zero('id_sale_price');
  let min_sale = value_or_zero('id_minimum_price');
  let total_cost = cost + restoration;
  let profit = sale - total_cost;
  let min_profit = min_sale - total_cost;
  let margin = 0;
  if (profit > 0) {
    margin = profit / sale * 100;
  }
  let min_margin = 0;
  if (min_sale > 0) {
    min_margin = min_profit / min_sale * 100;
  }
  $("#id_total_cost").val(total_cost).prop("readonly", true);
  $('#id_margin').html("Margin: " + margin.toFixed(2) + "%");
  $('#id_min_margin').html("Margin: " + min_margin.toFixed(2) + "%");
}

function value_or_zero(id) {
  let x = parseFloat(document.getElementById(id).value);
  if (isNaN(x)) {
    return 0;
  } else {
    return x;
  }
}