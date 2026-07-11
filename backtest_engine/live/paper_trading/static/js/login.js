// Check for URL query parameter error (handles password manager fallback redirect)
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('error') === 'true') {
    const errorAlert = document.getElementById('errorAlert');
    errorAlert.textContent = 'Identifiant ou mot de passe incorrect.';
    errorAlert.style.display = 'block';
}

console.log("login.js starting...");
const loginForm = document.getElementById('loginForm');
console.log("loginForm found:", !!loginForm);

if (loginForm) {
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log("Submit event triggered!");
    
    const submitBtn = document.getElementById('submitBtn');
    const errorAlert = document.getElementById('errorAlert');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    errorAlert.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Connexion...';
    
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
            const data = await response.json();
            errorAlert.textContent = data.message || 'Identifiant ou mot de passe incorrect.';
            errorAlert.style.display = 'block';
            passwordInput.value = '';
        }
    } catch (err) {
        errorAlert.textContent = 'Erreur de connexion au serveur. Veuillez réessayer.';
        errorAlert.style.display = 'block';
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Se connecter';
    }
});
}
