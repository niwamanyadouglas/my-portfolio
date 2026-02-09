// Initialize AOS (Animate on Scroll)
document.addEventListener('DOMContentLoaded', function () {
    AOS.init({
        duration: 1000, // Animation duration
        easing: 'ease-in-out', // Animation easing
        once: true, // Animate only once
    });

    // 1. Auto-hide Flash Messages (Success/Error Alerts)
    // This removes the message after 5 seconds so the user doesn't have to click 'x'
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.transition = "opacity 0.6s ease";
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 600);
        });
    }, 5000);
});

// 2. Smooth Scrolling for Anchor Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// 3. Navbar background change on scroll
// Adds a shadow and solid background when you scroll down
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('bg-dark', 'shadow');
    } else {
        navbar.classList.remove('shadow');
    }
});