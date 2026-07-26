// Check for URL query parameter error (handles password manager fallback redirect)
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('error') === 'true') {
    const errorAlert = document.getElementById('errorAlert');
    errorAlert.textContent = 'Invalid username or password.';
    errorAlert.style.display = 'block';
}

const loginForm = document.getElementById('loginForm');

if (loginForm) {
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const errorAlert = document.getElementById('errorAlert');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    errorAlert.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: usernameInput.value,
                password: passwordInput.value
            })
        });
        
        if (response.ok) {
            window.location.href = '/';
        } else {
            if (response.status === 429) {
                errorAlert.textContent = 'Too many login attempts. Please wait 5 minutes and try again.';
            } else {
                const data = await response.json();
                errorAlert.textContent = data.message || 'Invalid username or password.';
            }
            errorAlert.style.display = 'block';
            passwordInput.value = '';
        }
    } catch (err) {
        errorAlert.textContent = 'Server connection error. Please try again.';
        errorAlert.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Log In';
    }
});
}
