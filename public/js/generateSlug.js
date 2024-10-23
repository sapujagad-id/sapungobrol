document.addEventListener('DOMContentLoaded', function () {
    const nameInput = document.getElementById('name');
    const slugInput = document.getElementById('slug');
    
    function generateSlug(text) {
        return text
            .toString()
            .toLowerCase()
            .trim()
            .replace(/\s+/g, '-')     
            .replace(/[^\w-]+/g, '')   
            .replace(/--+/g, '-'); 
    }

    nameInput.addEventListener('input', function () {
        if (slugInput.dataset.userEdited === "false") {
            slugInput.value = generateSlug(nameInput.value);
        }
    });

    slugInput.addEventListener('input', function () {
        slugInput.dataset.userEdited = "true";
    });

    slugInput.addEventListener('blur', function () {
        if (slugInput.value.trim() === '') {
            slugInput.dataset.userEdited = "false";
            slugInput.value = generateSlug(nameInput.value);
        }
    });

    if (nameInput.value.trim() !== '') {
        slugInput.value = generateSlug(nameInput.value);
    }
});