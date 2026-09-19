// Custom JavaScript for Liga YGO Marabá

document.addEventListener('DOMContentLoaded', function() {
    
    // Enhanced cards smooth entrance handled cleanly without lag
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('fade-in');
    });

    // Theme Management (Light / Dark Mode)
    function updateThemeIcons(currentTheme) {
        const icons = document.querySelectorAll('.theme-icon');
        icons.forEach(icon => {
            if (currentTheme === 'dark') {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            } else {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
        });
    }

    const initialTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
    updateThemeIcons(initialTheme);

    const themeToggles = document.querySelectorAll('.js-theme-toggle');
    themeToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', next);
            localStorage.setItem('ygo-theme', next);
            updateThemeIcons(next);
            
            // Trigger custom event so charts can update their colors if present
            window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme: next } }));
        });
    });

    // Add loading animation to buttons on form submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !form.dataset.submitting) {
                form.dataset.submitting = 'true';
                const originalText = submitBtn.innerHTML;
                form.dataset.originalSubmitText = originalText;
                submitBtn.innerHTML = '<span class="loading"></span> Processando...';
                submitBtn.disabled = true;
            }
        });
    });



    // Add hover effects to table rows
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.2s ease';
        });
    });

    // Format numbers in forms
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value < 0) {
                this.value = 0;
                showToast('Valores negativos não são permitidos', 'warning');
            }
        });
    });

    // Search functionality enhancement
    const searchInputs = document.querySelectorAll('input[name="nome_busca"], input[name="nome_duelista"]');
    searchInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value.trim();
            if (value.length > 0) {
                this.style.borderColor = '#28a745';
            } else {
                this.style.borderColor = '#ced4da';
            }
        });
    });

    // Confirmation dialogs for sensitive actions (SweetAlert2)
    const dangerousButtons = document.querySelectorAll('[data-confirm]');
    dangerousButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const form = this.form;
            const alreadyConfirmed = this.dataset.confirmed === 'true';

            if (alreadyConfirmed) {
                this.dataset.confirmed = 'false';
                return;
            }

            e.preventDefault();

            const message = this.getAttribute('data-confirm') || 'Tem certeza que deseja continuar?';
            const title = this.getAttribute('data-confirm-title') || 'Confirmação';
            const icon = this.getAttribute('data-confirm-icon') || 'warning';
            const confirmText = this.getAttribute('data-confirm-confirm-text') || 'Confirmar';
            const cancelText = this.getAttribute('data-confirm-cancel-text') || 'Cancelar';

            if (window.Swal) {
                Swal.fire({
                    title: title,
                    text: message,
                    icon: icon,
                    showCancelButton: true,
                    confirmButtonText: confirmText,
                    cancelButtonText: cancelText,
                    reverseButtons: true,
                    focusCancel: true
                }).then(result => {
                    if (result.isConfirmed && form) {
                        this.dataset.confirmed = 'true';
                        if (typeof form.requestSubmit === 'function') {
                            form.requestSubmit();
                        } else {
                            form.submit();
                        }
                    }
                });
                return;
            }

            // Fallback if SweetAlert2 is unavailable
            if (confirm(message) && form) {
                this.dataset.confirmed = 'true';
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            }
        });
    });

    // Add smooth scrolling to anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Toast notification system
    function showToast(message, type = 'info') {
        const toastContainer = getToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
        `;
        
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.add('fade');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 4000);
    }

    function getToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    // Form validation enhancements
    const forms_validation = document.querySelectorAll('form');
    forms_validation.forEach(form => {
        const inputs = form.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateInput(this);
                }
            });
        });
    });

    function validateInput(input) {
        const value = input.value.trim();
        let isValid = true;
        let message = '';

        // Required field validation
        if (input.hasAttribute('required') && !value) {
            isValid = false;
            message = 'Este campo é obrigatório';
        }

        // Number validation
        if (input.type === 'number' && value && isNaN(value)) {
            isValid = false;
            message = 'Digite apenas números';
        }

        // Name validation (only letters and spaces) — applies only to duelista names
        if (input.name === 'nome_duelista') {
            if (value && !/^[a-zA-ZÀ-ÿ\s]+$/.test(value)) {
                isValid = false;
                message = 'Use apenas letras e espaços';
            }
        }

        // Update input styling
        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            removeErrorMessage(input);
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            showErrorMessage(input, message);
        }

        return isValid;
    }

    function showErrorMessage(input, message) {
        removeErrorMessage(input);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        
        input.parentNode.appendChild(errorDiv);
    }

    function removeErrorMessage(input) {
        const existingError = input.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }
    }

    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter submits only the currently focused form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeElement = document.activeElement;
            const activeForm = activeElement ? activeElement.closest('form') : null;
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        }
    });

    // Initialize tooltips and popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Expose useful functions globally
    window.YGOUtils = window.YGOUtils || {};
    window.YGOUtils.showToast = showToast;
    window.YGOUtils.validateInput = validateInput;
});

/**
 * Utilitários de captura e exportação de imagem para Liga YGO Marabá
 */
async function baixarElementoComoImagem({
    cardEl,
    filename = 'imagem.png',
    modalId = null,
    triggerBtn = null,
    backgroundColor = null,
    loadingText = 'Gerando imagem...'
} = {}) {
    const targetEl = typeof cardEl === 'string' ? document.getElementById(cardEl) : cardEl;
    if (!targetEl) {
        console.error('Elemento não encontrado para baixar imagem:', cardEl);
        return;
    }

    const btnEl = typeof triggerBtn === 'string' ? document.getElementById(triggerBtn) : triggerBtn;
    let originalHtml = '';
    if (btnEl) {
        originalHtml = btnEl.innerHTML;
        btnEl.disabled = true;
        btnEl.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> ${loadingText}`;
    }

    try {
        if (typeof html2canvas === 'undefined') {
            throw new Error('html2canvas não está carregado.');
        }

        const html2canvasOptions = {
            scale: 2,
            useCORS: true,
            backgroundColor: backgroundColor !== undefined ? backgroundColor : null,
            scrollY: 0,
            scrollX: 0
        };

        if (targetEl.scrollWidth && targetEl.scrollHeight) {
            html2canvasOptions.windowWidth = targetEl.scrollWidth;
            html2canvasOptions.windowHeight = targetEl.scrollHeight;
        }

        const cleanModalId = typeof modalId === 'string' ? modalId.replace(/^#/, '') : (modalId && modalId.id ? modalId.id : null);
        if (cleanModalId) {
            html2canvasOptions.onclone = (clonedDoc) => {
                const modalEl = clonedDoc.getElementById(cleanModalId);
                if (modalEl) {
                    modalEl.querySelectorAll('.modal-dialog, .modal-content, .modal-body').forEach(el => {
                        el.style.maxHeight = 'none';
                        el.style.overflow = 'visible';
                        el.style.height = 'auto';
                    });
                }
            };
        }

        const canvas = await html2canvas(targetEl, html2canvasOptions);
        const link = document.createElement('a');
        link.download = filename || 'imagem.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    } catch (err) {
        console.error('Erro ao gerar/baixar imagem:', err);
        alert('Não foi possível gerar a imagem.');
    } finally {
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
        }
    }
}

async function compartilharElementoComoImagem({
    cardEl,
    filename = 'compartilhamento.png',
    title = 'Liga YGO Marabá',
    text = '',
    url = window.location.href,
    modalId = null,
    triggerBtn = null,
    backgroundColor = null,
    loadingText = 'Preparando imagem...'
} = {}) {
    const targetEl = typeof cardEl === 'string' ? document.getElementById(cardEl) : cardEl;
    if (!targetEl) {
        console.error('Elemento não encontrado para compartilhar:', cardEl);
        return;
    }

    const btnEl = typeof triggerBtn === 'string' ? document.getElementById(triggerBtn) : triggerBtn;
    let originalHtml = '';
    if (btnEl) {
        originalHtml = btnEl.innerHTML;
        btnEl.disabled = true;
        btnEl.innerHTML = `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> ${loadingText}`;
    }

    try {
        if (typeof html2canvas === 'undefined') {
            throw new Error('html2canvas não está carregado.');
        }

        const shareUrl = url || window.location.href;
        let fullText = text || '';
        if (shareUrl && !fullText.includes(shareUrl)) {
            fullText = fullText ? `${fullText}\n${shareUrl}` : shareUrl;
        }

        const html2canvasOptions = {
            scale: 2,
            useCORS: true,
            backgroundColor: backgroundColor !== undefined ? backgroundColor : null,
            scrollY: 0,
            scrollX: 0
        };

        if (targetEl.scrollWidth && targetEl.scrollHeight) {
            html2canvasOptions.windowWidth = targetEl.scrollWidth;
            html2canvasOptions.windowHeight = targetEl.scrollHeight;
        }

        const cleanModalId = typeof modalId === 'string' ? modalId.replace(/^#/, '') : (modalId && modalId.id ? modalId.id : null);
        if (cleanModalId) {
            html2canvasOptions.onclone = (clonedDoc) => {
                const modalEl = clonedDoc.getElementById(cleanModalId);
                if (modalEl) {
                    modalEl.querySelectorAll('.modal-dialog, .modal-content, .modal-body').forEach(el => {
                        el.style.maxHeight = 'none';
                        el.style.overflow = 'visible';
                        el.style.height = 'auto';
                    });
                }
            };
        }

        const canvas = await html2canvas(targetEl, html2canvasOptions);
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
        if (!blob) throw new Error('Não foi possível gerar a imagem.');

        const saveFilename = filename || 'compartilhamento.png';
        const file = new File([blob], saveFilename, { type: 'image/png' });

        // 1. Tenta compartilhar via Web Share API com anexo de arquivo
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
            try {
                await navigator.share({
                    title: title,
                    text: fullText,
                    files: [file]
                });
                return;
            } catch (shareErr) {
                if (shareErr.name === 'AbortError') return;
                console.warn('Web Share com arquivos falhou:', shareErr);
            }
        }

        // 2. Se não puder compartilhar arquivos, mas suportar Web Share de texto/link
        if (navigator.share) {
            try {
                const link = document.createElement('a');
                link.download = saveFilename;
                link.href = canvas.toDataURL('image/png');
                link.click();

                await navigator.share({
                    title: title,
                    text: `${fullText}\n(A imagem foi salva em seus downloads!)`,
                    url: shareUrl
                });
                return;
            } catch (shareErr) {
                if (shareErr.name === 'AbortError') return;
            }
        }

        // 3. Fallback para desktop sem suporte a Web Share (download + cópia para Clipboard + WhatsApp)
        const link = document.createElement('a');
        link.download = saveFilename;
        link.href = canvas.toDataURL('image/png');
        link.click();

        if (navigator.clipboard && window.ClipboardItem) {
            try {
                await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
            } catch (e) {
                // ClipboardItem pode não ser suportado ou rejeitado por permissão
            }
        }

        window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(fullText)}`, '_blank');
    } catch (err) {
        console.error('Erro ao compartilhar:', err);
        alert('Não foi possível gerar a imagem para compartilhamento.');
    } finally {
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.innerHTML = originalHtml;
        }
    }
}

window.YGOUtils = window.YGOUtils || {};
window.YGOUtils.baixarElementoComoImagem = baixarElementoComoImagem;
window.YGOUtils.compartilharElementoComoImagem = compartilharElementoComoImagem;

// Additional utilities
function formatNumber(num) {
    return new Intl.NumberFormat('pt-BR').format(num);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
}