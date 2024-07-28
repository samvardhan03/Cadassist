// Function to handle button clicks
function showMessage(message) {
    alert(message);
}

// Function to handle sending a message from the input field
function sendMessage(event) {
    if (event.type === 'keypress' && event.key !== 'Enter') {
        return;
    }

    const input = document.getElementById('userInput');
    const message = input.value.trim();

    if (message) {
        alert(`You typed: ${message}`);
        input.value = ''; // Clear the input field
    }
}
