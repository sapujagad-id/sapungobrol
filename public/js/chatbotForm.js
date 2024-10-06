function validateForm() {
    const name = document.getElementById('name').value;
    const systemPrompt = document.getElementById('system_prompt').value;
    const model = document.getElementById('model').value;
    const adapter = document.getElementById('adapter').value;

    if (name === "" || systemPrompt === "" || model === "" || adapter === "") {
        return false;
    }

    return isValidInput(name) && isValidInput(systemPrompt);

}

function isValidInput(input) {
    const sqlInjectionPattern = /['";-]/; 
    return !sqlInjectionPattern.test(input);
}

async function submitForm(event, bot_id = null) {
    event.preventDefault();  // Prevent the form from submitting the old way (e.g., to /edit/{bot_id})

    // Validate form inputs
    if (!validateForm()) {
        alert('Error: Please check your input!');
        return;
    }

    // Collect form data
    const formData = {
        name: document.getElementById('name').value,
        system_prompt: document.getElementById('system_prompt').value,
        model: document.getElementById('model').value,
        adapter: document.getElementById('adapter').value
    };

    // Determine the method and URL
    let method = bot_id ? 'PATCH' : 'POST';  // PATCH if bot_id exists, POST otherwise
    let url = bot_id ? `/api/bots/${bot_id}` : '/api/bots';  // Use bot_id if editing, otherwise create new

    // Send the request to the correct API endpoint
    const response = await fetch(url, {
        method: method,  
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    const result = await response.json();

    // Handle response
    if (response.ok) {
        alert(bot_id ? 'Chatbot updated successfully!' : 'Chatbot created successfully!');
        window.location.href = '/';
    } else {
        alert(`Error: ${result.detail}`);
    }
}

