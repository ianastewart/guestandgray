function margin_calc() {
    let cost = int_or_zero("id_cost_price");
    let restoration = int_or_zero("id_restoration_cost");
    let sale = int_or_zero('id_sale_price');
    let min_sale = int_or_zero('id_minimum_price');
    let total_cost = cost + restoration;
    let profit = sale - total_cost;
    let min_profit = min_sale - total_cost;
    let margin = parseInt(profit / sale * 1000) / 10;
    let min_margin = parseInt(min_profit / min_sale * 1000) / 10;
    $('#id_restoration_cost').val(restoration / 100);
    $('#id_sale_price').val(sale / 100);
    $('#id_minimum_price').val(min_sale / 100);
    $("#id_total_cost").html("£" + total_cost / 100);
    $('#id_margin').html(margin + "%");
    $('#id_min_margin').html(min_margin + "%");
}

function int_or_zero(id) {
    let x = parseInt(document.getElementById(id).value);
    if (isNaN(x)) {
        return 0;
    } else {
        return x * 100;
    }
}