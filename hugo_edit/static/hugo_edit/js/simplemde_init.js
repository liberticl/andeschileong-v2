document.addEventListener("DOMContentLoaded", function() {
    var contentField = document.getElementById("id_content");
    if (contentField) {
        var simplemde = new SimpleMDE({ element: contentField });
    }
});
