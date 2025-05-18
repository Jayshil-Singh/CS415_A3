function showAlert(action) {
    alert(`Action: ${action} (Functionality would be implemented here)`);
    // In a real application, this would trigger the actual functionality
}

// Basic JavaScript to toggle the drawer
const drawer = document.querySelector('.drawer');
const header = document.querySelector('.header'); // Assuming you want to trigger from the header

header.addEventListener('click', () => {
    drawer.classList.toggle('open');
});