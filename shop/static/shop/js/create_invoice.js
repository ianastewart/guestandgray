$(document).ready(function () {
    $("#id_proforma").val(false)
    $("#radio_invoice").prop("checked",true);
    $("#id_date_group").show();

    $("#radio_proforma").click(function() {
        $("#id_date_group").hide();
        $("#id_proforma").val(true);
        $("#create_button").html("Create proforma invoice")
    });
    $("#radio_invoice").click(function() {
    $("#id_date_group").show();
    $("#id_proforma").val(false)
    $("#create_button").html("Create final invoice")
    });
});