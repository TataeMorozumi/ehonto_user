document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("addBookForm");

    if (form) {
        form.addEventListener("submit", function (event) {
            setTimeout(function() {
                location.reload();  // ✅ 登録後にページをリロードして最新のデータを表示
            }, 500);
        });
    }
});
