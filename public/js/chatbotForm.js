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

    const formData = {
        name: document.getElementById('name').value,
        system_prompt: document.getElementById('system_prompt').value,
        model: document.getElementById('model').value,
        adapter: document.getElementById('adapter').value,
        slug: document.getElementById('slug').value
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

