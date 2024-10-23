async function confirmDelete(bot_id) {
    if (!confirm("Are you sure you want to delete this bot? This action cannot be undone.")) {
        return;
    }

    let method = 'DELETE';
    let url = `/api/bots/${bot_id}`;

    const response = await fetch(url, {
        method: method
    });

    if (response.status === 204) {
        alert('Chatbot deleted successfully!');
        window.location.href = '/';
    } else {
        const result = await response.json();
        alert(`Error: ${result.detail}`);
        window.location.href = '/';
    }
}