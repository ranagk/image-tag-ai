/* ==========================================================================
   ImageTag AI - Main JavaScript File
   ==========================================================================
   TABLE OF CONTENTS
   01. DOM Ready Wrapper
   02. Alert Auto-Hide
   03. Image Upload Preview
   04. Drag & Drop Support
   05. Remove Image Button
   06. File Validation (Type + Size)
   07. Form Submit Loading State
   08. Delete Confirmation
   09. Password Match Validation (Signup)
   10. Password Strength Indicator
   11. Mobile Menu Toggle
   12. Smooth Scroll
   13. Search Input Auto-Focus
   14. Auto-dismiss Flash Messages
   15. Console Safety Check
   ========================================================================== */


/* ==========================================================================
   01. DOM READY WRAPPER
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function () {
    initAlertAutoHide();
    initImageUpload();
    initDragAndDrop();
    initFormSubmitLoading();
    initDeleteConfirmation();
    initPasswordMatch();
    initPasswordStrength();
    initMobileMenu();
    initSmoothScroll();
    initSearchFocus();
});


/* ==========================================================================
   02. ALERT AUTO-HIDE
   ========================================================================== */
/* Har alert message 5 second baad khud gayab ho jaye */

function initAlertAutoHide() {
    // Dekho ke koi alert mojood hai jo Flask/Jinja ne banaya hai
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {
        // Agar alert pehle se styled nahi hai, to usko "Toast" banado
        if (!alert.classList.contains("toast-alert")) {
            alert.classList.add("toast-alert");
            alert.style.position = "fixed";
            alert.style.top = "20px";
            alert.style.right = "20px";
            alert.style.zIndex = "9999";
            alert.style.boxShadow = "0 10px 25px rgba(0,0,0,0.15)";
            alert.style.animation = "slideInRight 0.3s ease forwards";
            alert.style.width = "320px";
            alert.style.margin = "0";
        }

        // 3.5 second baad gayab ho jaye
        setTimeout(function () {
            alert.style.transition = "opacity 0.5s ease, transform 0.5s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateX(100%)";

            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 3500); // 3.5 seconds
    });
}

// CSS Animation add karne ke liye
const style = document.createElement('style');
style.innerHTML = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);


/* ==========================================================================
   03. IMAGE UPLOAD PREVIEW
   ========================================================================== */
/* Jab user image select kare, uska preview dikhao */

function initImageUpload() {
    const imageInput = document.getElementById("analysisImageInput");
    const imagePreview = document.getElementById("analysisPreview");
    const previewImage = document.getElementById("analysisPreviewImage");
    const uploadPrompt = document.getElementById("uploadPrompt");
    const changeBtn = document.getElementById("changeImage");
    const fileNameEl = document.getElementById("selectedFileName");
    const fileSizeEl = document.getElementById("selectedFileSize");
    const fileErrorEl = document.getElementById("fileError");

    if (!imageInput) return;

    // File select hone pe
    imageInput.addEventListener("change", function (event) {
        const file = event.target.files[0];
        if (!file) return;

        // Purana error hata do
        if (fileErrorEl) fileErrorEl.style.display = "none";

        // File validate karo
        const validation = validateFile(file);
        if (!validation.valid) {
            if (fileErrorEl) {
                fileErrorEl.textContent = validation.message;
                fileErrorEl.style.display = "block";
                setTimeout(function () {
                    fileErrorEl.style.display = "none";
                }, 5000);
            }
            imageInput.value = "";
            return;
        }

        // Preview dikhao
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImage.src = e.target.result;
            imagePreview.style.display = "block";
            if (uploadPrompt) uploadPrompt.style.display = "none";
            if (fileNameEl) fileNameEl.textContent = file.name;
            if (fileSizeEl) fileSizeEl.textContent = formatFileSize(file.size);
        };
        reader.readAsDataURL(file);
    });

    // Change image button
    if (changeBtn) {
        changeBtn.addEventListener("click", function (e) {
            e.preventDefault();
            resetUpload();
        });
    }

    function resetUpload() {
        imageInput.value = "";
        previewImage.src = "";
        imagePreview.style.display = "none";
        if (uploadPrompt) uploadPrompt.style.display = "block";
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }
}function initImageUpload() {
    const imageInput = document.getElementById("analysisImageInput");
    const imagePreview = document.getElementById("analysisPreview");
    const previewImage = document.getElementById("analysisPreviewImage");
    const uploadPrompt = document.getElementById("uploadPrompt");
    const changeBtn = document.getElementById("changeImage");
    const fileNameEl = document.getElementById("selectedFileName");
    const fileSizeEl = document.getElementById("selectedFileSize");
    const fileErrorEl = document.getElementById("fileError");

    if (!imageInput) return;

    // File select hone pe
    imageInput.addEventListener("change", function (event) {
        const file = event.target.files[0];
        if (!file) return;

        // Purana error hata do
        if (fileErrorEl) fileErrorEl.style.display = "none";

        // File validate karo
        const validation = validateFile(file);
        if (!validation.valid) {
            if (fileErrorEl) {
                fileErrorEl.textContent = validation.message;
                fileErrorEl.style.display = "block";
                setTimeout(function () {
                    fileErrorEl.style.display = "none";
                }, 5000);
            }
            imageInput.value = "";
            return;
        }

        // Preview dikhao
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImage.src = e.target.result;
            imagePreview.style.display = "block";
            if (uploadPrompt) uploadPrompt.style.display = "none";
            if (fileNameEl) fileNameEl.textContent = file.name;
            if (fileSizeEl) fileSizeEl.textContent = formatFileSize(file.size);
        };
        reader.readAsDataURL(file);
    });

    // Change image button
    if (changeBtn) {
        changeBtn.addEventListener("click", function (e) {
            e.preventDefault();
            resetUpload();
        });
    }

    function resetUpload() {
        imageInput.value = "";
        previewImage.src = "";
        imagePreview.style.display = "none";
        if (uploadPrompt) uploadPrompt.style.display = "block";
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }
}

/* ==========================================================================
   04. DRAG & DROP SUPPORT
   ========================================================================== */
/* User image ko drag karke drop kar sake */

function initDragAndDrop() {
    const dropzone = document.getElementById("largeDropzone");
    const imageInput = document.getElementById("analysisImageInput");

    if (!dropzone || !imageInput) return;

    // Jab file dropzone ke upar aaye
    ["dragenter", "dragover"].forEach(function (eventName) {
        dropzone.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        });
    });

    // Jab file dropzone se bahar jaye
    ["dragleave", "drop"].forEach(function (eventName) {
        dropzone.addEventListener(eventName, function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        });
    });

    // Jab file drop ho
    dropzone.addEventListener("drop", function (e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            imageInput.files = files;
            const changeEvent = new Event("change", { bubbles: true });
            imageInput.dispatchEvent(changeEvent);
        }
    });
}

/* ==========================================================================
   05. FILE VALIDATION (TYPE + SIZE)
   ========================================================================== */

const ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png"];
const ALLOWED_EXTENSIONS = ["jpg", "jpeg", "png"];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

function validateFile(file) {
    // Extension check
    const extension = file.name.split(".").pop().toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
        return {
            valid: false,
            message: "❌ Invalid file format. Only JPG, JPEG, and PNG are allowed."
        };
    }

    // MIME type check
    if (!ALLOWED_TYPES.includes(file.type)) {
        return {
            valid: false,
            message: "❌ Invalid file type. Please upload a valid image."
        };
    }

    // Size check
    if (file.size > MAX_FILE_SIZE) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        return {
            valid: false,
            message: "❌ File too large (" + sizeMB + " MB). Maximum allowed is 5 MB."
        };
    }

    return { valid: true, message: "" };
}

function showInlineError(message) {
    // Purana error hata do
    const oldError = document.querySelector(".js-inline-error");
    if (oldError) oldError.remove();

    // Naya error banao
    const errorDiv = document.createElement("div");
    errorDiv.className = "alert alert-error js-inline-error";
    errorDiv.setAttribute("role", "alert");
    errorDiv.textContent = message;

    // Dropzone ke upar insert karo
    const dropzone = document.getElementById("largeDropzone");  
    if (dropzone && dropzone.parentNode) {
        dropzone.parentNode.insertBefore(errorDiv, dropzone);
    }

    // 5 second baad auto-remove
    setTimeout(function () {
        if (errorDiv.parentNode) {
            errorDiv.style.transition = "opacity 0.5s";
            errorDiv.style.opacity = "0";
            setTimeout(function () {
                if (errorDiv.parentNode) errorDiv.remove();
            }, 500);
        }
    }, 5000);
}


/* ==========================================================================
   06. FORM SUBMIT LOADING STATE
   ========================================================================== */
/* Form submit hone pe button disable + spinner */

function initFormSubmitLoading() {
    const forms = document.querySelectorAll("form");

    forms.forEach(function (form) {
        form.addEventListener("submit", function (e) {
            // Sirf upload/analyze form pe loading dikhao
            const submitBtn = form.querySelector("button[type='submit']");
            if (!submitBtn) return;

            // Agar form me file input hai to loading dikhao
            const fileInput = form.querySelector("input[type='file']");

            if (fileInput) {
                // File select nahi hui to rok do
                if (!fileInput.files || fileInput.files.length === 0) {
                    return;
                }

                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.textContent;
                submitBtn.innerHTML = "⏳ Analyzing... (3-5 sec)";
                submitBtn.style.opacity = "0.7";
                submitBtn.style.cursor = "not-allowed";
            }
        });
    });
}


/* ==========================================================================
   07. DELETE CONFIRMATION
   ========================================================================== */
/* Delete button pe click karne se pehle "Are you sure?" */

function initDeleteConfirmation() {
    // Use event delegation — har form pe alag listener nahi lagana padega
    document.body.addEventListener("submit", function (e) {
        const form = e.target;

        // Check karo delete form hai?
        if (!form.classList.contains("delete-history-form")) {
            return;
        }

        // Popup dikhao
        const message = form.dataset.confirm ||
            "Are you sure you want to delete this analysis?";

        const confirmed = window.confirm(message);

        if (!confirmed) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
    });

    console.log("✅ Delete confirmation listener attached");
}


/* ==========================================================================
   08. PASSWORD MATCH VALIDATION (SIGNUP)
   ========================================================================== */

function initPasswordMatch() {
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm_password");

    if (!passwordInput || !confirmInput) return;

    function checkMatch() {
        if (confirmInput.value.length === 0) {
            confirmInput.setCustomValidity("");
            return;
        }

        if (passwordInput.value !== confirmInput.value) {
            confirmInput.setCustomValidity("Passwords do not match.");
        } else {
            confirmInput.setCustomValidity("");
        }
    }

    passwordInput.addEventListener("input", checkMatch);
    confirmInput.addEventListener("input", checkMatch);
}


/* ==========================================================================
   09. PASSWORD STRENGTH INDICATOR
   ========================================================================== */

function initPasswordStrength() {
    const newPassword = document.getElementById("new_password");
    const signupPassword = document.getElementById("password");

    const targetInput = newPassword || signupPassword;
    if (!targetInput) return;

    const strengthBar = document.createElement("div");
    strengthBar.className = "password-strength";
    strengthBar.style.height = "4px";
    strengthBar.style.marginTop = "8px";
    strengthBar.style.borderRadius = "2px";
    strengthBar.style.transition = "all 0.3s ease";

    targetInput.parentNode.appendChild(strengthBar);

    targetInput.addEventListener("input", function () {
        const value = targetInput.value;
        const strength = calculateStrength(value);

        if (value.length === 0) {
            strengthBar.style.width = "0%";
            strengthBar.style.backgroundColor = "transparent";
            return;
        }

        strengthBar.style.width = "100%";

        if (strength === "weak") {
            strengthBar.style.backgroundColor = "#dc2626";
        } else if (strength === "medium") {
            strengthBar.style.backgroundColor = "#f59e0b";
        } else {
            strengthBar.style.backgroundColor = "#16a34a";
        }
    });
}

function calculateStrength(password) {
    let score = 0;

    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score <= 2) return "weak";
    if (score <= 4) return "medium";
    return "strong";
}


/* ==========================================================================
   10. MOBILE MENU TOGGLE
   ========================================================================== */

function initMobileMenu() {
    const navMenu = document.querySelector(".nav-menu");
    const navContainer = document.querySelector(".nav-container");

    if (!navMenu || !navContainer) return;

    // Hamburger button banao
    const hamburger = document.createElement("button");
    hamburger.className = "hamburger";
    hamburger.setAttribute("aria-label", "Toggle navigation menu");
    hamburger.innerHTML = "☰";
    hamburger.style.display = "none";
    hamburger.style.background = "none";
    hamburger.style.border = "none";
    hamburger.style.fontSize = "1.5rem";
    hamburger.style.cursor = "pointer";
    hamburger.style.color = "#4f46e5";

    navContainer.insertBefore(hamburger, navMenu);

    // Screen size check karo
    function checkScreen() {
        if (window.innerWidth <= 640) {
            hamburger.style.display = "block";
            navMenu.style.display = "none";
        } else {
            hamburger.style.display = "none";
            navMenu.style.display = "flex";
        }
    }

    hamburger.addEventListener("click", function () {
        if (navMenu.style.display === "none") {
            navMenu.style.display = "flex";
            navMenu.style.flexDirection = "column";
            navMenu.style.width = "100%";
            navMenu.style.marginTop = "12px";
        } else {
            navMenu.style.display = "none";
        }
    });

    window.addEventListener("resize", checkScreen);
    checkScreen();
}


/* ==========================================================================
   11. SMOOTH SCROLL
   ========================================================================== */

function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(function (link) {
        link.addEventListener("click", function (e) {
            const targetId = link.getAttribute("href");
            if (targetId === "#") return;

            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });
}


/* ==========================================================================
   12. SEARCH INPUT AUTO-FOCUS
   ========================================================================== */
/* History page pe search box pe auto-focus */

function initSearchFocus() {
    const searchInput = document.querySelector('input[type="search"]');
    if (!searchInput) return;

    // Agar URL me search query hai to focus mat karo
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("search")) return;

    // Warna focus karo
    searchInput.focus();
}


/* ==========================================================================
   13. CONSOLE SAFETY CHECK
   ========================================================================== */
/* Development ke doran console me confirm karo ke JS load hua */

console.log("✅ ImageTag AI - script.js loaded successfully");

/* ==========================================================================
   DASHBOARD IMAGE PREVIEW (Dashboard.html specific)
   ========================================================================== */
document.addEventListener("DOMContentLoaded", function () {
    const dashInput = document.getElementById("imageInput");
    const dashPreview = document.getElementById("imagePreview");
    const dashPreviewImg = document.getElementById("previewImage");
    const dashLabel = document.getElementById("uploadLabel");
    const dashRemoveBtn = document.getElementById("removeImage");

    // Agar dashboard ke elements mil gaye hain toh ye code chale
    if (dashInput && dashPreview) {
        dashInput.addEventListener("change", function (event) {
            const file = event.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function (e) {
                dashPreviewImg.src = e.target.result;
                dashPreview.style.display = "block";
                if (dashLabel) dashLabel.style.display = "none";
            };
            reader.readAsDataURL(file);
        });

        if (dashRemoveBtn) {
            dashRemoveBtn.addEventListener("click", function (e) {
                e.preventDefault();
                dashInput.value = "";
                dashPreviewImg.src = "";
                dashPreview.style.display = "none";
                if (dashLabel) dashLabel.style.display = "block";
            });
        }
    }
});

/* =========================================================
   THEME HANDLING (Dark/Light/System)
   ========================================================= 
document.addEventListener("DOMContentLoaded", function () {
    // 1. HTML tag se database ki theme uthao (jo Flask ne bheji hai)
    let currentTheme = document.documentElement.getAttribute("data-theme");
    
    // 2. Agar local storage me theme hai, to wahan se uthao
    let savedTheme = localStorage.getItem("theme");
    
    // 3. Agar local storage me hai to usko use karo, warna database wali lagao
    let finalTheme = savedTheme || currentTheme || "light";

    // 4. Apply karo
    if (finalTheme === "system") {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute("data-theme", "dark");
        } else {
            document.documentElement.setAttribute("data-theme", "light");
        }
    } else {
        document.documentElement.setAttribute("data-theme", finalTheme);
    }
}); */
/* =========================================================
   GLOBAL THEME LOADER
   ========================================================= */
document.addEventListener("DOMContentLoaded", function () {
    // 1. Pehle check karo ke database (HTML) se kya theme aayi hai
    let dbTheme = document.documentElement.getAttribute("data-theme");
    
    // 2. LocalStorage se theme uthao
    let localTheme = localStorage.getItem("theme");
    
    // 3. Agar local storage me theme hai, to usko apply karo (Login page ke liye zaroori)
    if (localTheme) {
        document.documentElement.setAttribute("data-theme", localTheme);
    } else if (dbTheme) {
        document.documentElement.setAttribute("data-theme", dbTheme);
    }
});


/* =========================================================
   GLOBAL LANGUAGE SWITCHER LOGIC (Fast & Clean)
   ========================================================= */
function changeLanguage() {
    const lang = document.getElementById("languageSelect").value;
    
    // Cookie set karo
    if (lang === "en") {
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; domain=" + window.location.hostname + "; path=/;";
    } else {
        document.cookie = "googtrans=/en/" + lang + "; path=/";
        document.cookie = "googtrans=/en/" + lang + "; domain=" + window.location.hostname + "; path=/";
    }
    
    // Page reload karo
    window.location.reload();
}

document.addEventListener("DOMContentLoaded", function() {
    // Dropdown update karo
    const select = document.getElementById("languageSelect");
    if (select) {
        const match = document.cookie.match(/googtrans=\/en\/([a-zA-Z-]+)/);
        if (match && match[1]) {
            select.value = match[1];
        } else {
            select.value = "en";
        }
    }

    // Automatic Translate on Every Page
    const cookieMatch = document.cookie.match(/googtrans=\/en\/([a-zA-Z-]+)/);
    if (cookieMatch && cookieMatch[1] && cookieMatch[1] !== 'en') {
        
        // Google translate ko jaldi load karo
        window.googleTranslateElementInit = function() {
            new google.translate.TranslateElement({
                pageLanguage: 'en',
                includedLanguages: 'en,ur,fr,es,zh-CN,ar',
                autoDisplay: false
            }, 'google_translate_element');
        };
        
        const script = document.createElement('script');
        script.src = `//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit&lang=${cookieMatch[1]}`;
        document.body.appendChild(script);
        
        // FIX: Page ko chupao jab tak translate na ho (taake flicker na ho)
        document.documentElement.style.visibility = "hidden";
        setTimeout(function() {
            document.documentElement.style.visibility = "visible";
        }, 200); // Sirf 0.2 second ka delay
    }
});