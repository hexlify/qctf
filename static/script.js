$(document).ready(function () {
    $(".navbar-burger").click(function () {
        $(".navbar-burger").toggleClass("is-active");
        $(".navbar-menu").toggleClass("is-active");
    });

    $('.file-input')
        .on('change', function () {
            if (this.files.length > 0) {
                $('.file-name').text(this.files[0].name);
            }
        });
});