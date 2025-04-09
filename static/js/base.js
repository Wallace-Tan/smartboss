document.addEventListener('DOMContentLoaded', function() {
    const sidebarLinks = document.querySelectorAll('.side-bar li a');
    const currentPath = window.location.pathname;

    function setActiveLink(path) {
        sidebarLinks.forEach(link => {
            link.parentElement.classList.remove('active');
            if (link.getAttribute('href') === path) {
                link.parentElement.classList.add('active');
            }
        });
    }

    if (currentPath === '/') {
         setActiveLink(''); 
    } else {
        setActiveLink(currentPath);
    }

    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            sidebarLinks.forEach(link => {
              link.parentElement.classList.remove('active');
            })
            this.parentElement.classList.add('active');
        });
    });
});