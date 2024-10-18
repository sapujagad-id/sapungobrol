document.addEventListener('DOMContentLoaded', function () {
    const nameInput = document.getElementById('name');
    const slugInput = document.getElementById('slug');
    
    // Function to generate slug from the name
    function generateSlug(text) {
        return text
            .toString()
            .toLowerCase()
            .trim()
            .replace(/\s+/g, '-')     
            .replace(/[^\w-]+/g, '')   
            .replace(/--+/g, '-'); 
    }

    // Update the slug input as the name changes
    nameInput.addEventListener('input', function () {
        if (slugInput.dataset.userEdited === "false") {
            slugInput.value = generateSlug(nameInput.value);
        }
    });

    // Detect manual changes to the slug field
    slugInput.addEventListener('input', function () {
        slugInput.dataset.userEdited = "true";
    });

    // Reset the userEdited flag if the slug is cleared
    slugInput.addEventListener('blur', function () {
        if (slugInput.value.trim() === '') {
            slugInput.dataset.userEdited = "false";
            slugInput.value = generateSlug(nameInput.value);
        }
    });

    // Ensure slug updates immediately when the page loads if the name is already filled
    if (nameInput.value.trim() !== '') {
        slugInput.value = generateSlug(nameInput.value);
    }
});