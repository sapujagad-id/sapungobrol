document.addEventListener("DOMContentLoaded", function() {
    const dataSourceSelect = new TomSelect("#data_source", {
        plugins: ['remove_button'],
        create: false, 
        placeholder: "Select data sources...",
    });

    dataSourceSelect.on('change', function(values) {
        document.getElementById("data_source").value = values
        console.log('Selected values:', values);
    });
});

function validateForm() {
    const name = document.getElementById('name').value;
    const systemPrompt = document.getElementById('system_prompt').value;
    const model = document.getElementById('model').value;
    const adapter = document.getElementById('adapter').value;
    const slug = document.getElementById('slug').value

    if (name === "" || systemPrompt === "" || model === "" || adapter === "" || slug === "") {
        return false;
    }

    return isValidInput(name) && isValidInput(systemPrompt);

}

function isValidInput(input) {
    const sqlInjectionPattern = /['";-]/; 
    return !sqlInjectionPattern.test(input);
}

async function submitForm(event, bot_id = null) {
    event.preventDefault();  

    // Validate form inputs
    if (!validateForm()) {
        alert('Error: Please check your input!');
        return;
    }
    console.log(document.getElementById('data_source').value)
    const formData = {
        name: document.getElementById('name').value,
        system_prompt: document.getElementById('system_prompt').value,
        model: document.getElementById('model').value,
        adapter: document.getElementById('adapter').value,
        slug: document.getElementById('slug').value,
        data_source: document.getElementById('data_source').value
    };

    let method = bot_id ? 'PATCH' : 'POST';  // PATCH if bot_id exists, POST otherwise
    let url = bot_id ? `/api/bots/${bot_id}` : '/api/bots';  // Use bot_id if editing, otherwise create new

    const response = await fetch(url, {
        method: method,  
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    const result = await response.json();

    if (response.ok) {
        alert(bot_id ? 'Chatbot updated successfully!' : 'Chatbot created successfully!');
        window.location.href = '/';
    } else {
        alert(`Error: ${result.detail}`);
    }
}
async function checkSlug() {
    const slug = document.getElementById('slug').value;
    const resultElement = document.getElementById('slug-verification-result');

    if (slug === "") {
        resultElement.textContent = "Slug cannot be empty.";
        resultElement.classList.remove('text-green-500');
        resultElement.classList.add('text-red-500');
        return;
    }

    try {
        const response = await fetch(`/api/bots/slug?q=${encodeURIComponent(slug)}`);
        const data = await response.json();
        console.log(data)
        if (data.detail) {
            resultElement.textContent = "Slug already exists. Please choose another.";
            resultElement.classList.remove('text-green-500');
            resultElement.classList.add('text-red-500');
        } else {
            resultElement.textContent = "Slug is unique!";
            resultElement.classList.remove('text-red-500');
            resultElement.classList.add('text-green-500');
        }
    } catch (error) {
        resultElement.textContent = "Error checking slug. Please try again.";
        resultElement.classList.add('text-red-500');
    }
}

