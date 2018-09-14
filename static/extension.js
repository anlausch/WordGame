$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});


$('.btn').on('click', function() {
   $("#fakeloader").fakeLoader({

        timeToHide: 1200000,

        zIndex: "999",

        spinner: "spinner1",

        bgColor: "#a5d6a7"
    });
});