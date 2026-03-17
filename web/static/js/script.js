// Custom JavaScript for Liga YGO Marabá

document.addEventListener('DOMContentLoaded', function() {
    
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.6s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Add loading animation to buttons on form submit
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="loading"></span> Processando...';
                submitBtn.disabled = true;
                
                // Re-enable button after 3 seconds in case of error
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 3000);
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(() => {
                alert.style.transition = 'all 0.5s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-20px)';
                setTimeout(() => {
                    alert.remove();
                }, 500);
            }, 5000);
        }
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

    // Confirmation dialogs for destructive actions
    const dangerousButtons = document.querySelectorAll('[data-confirm]');
    dangerousButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Tem certeza que deseja continuar?';
            if (!confirm(message)) {
                e.preventDefault();
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

    // Dynamic table sorting (if needed)
    function sortTable(table, column, ascending = true) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        rows.sort((a, b) => {
            const aVal = a.cells[column].textContent.trim();
            const bVal = b.cells[column].textContent.trim();
            
            if (!isNaN(aVal) && !isNaN(bVal)) {
                return ascending ? aVal - bVal : bVal - aVal;
            }
            
            return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        });
        
        rows.forEach(row => tbody.appendChild(row));
    }

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

        // Name validation (only letters and spaces)
        if (input.name === 'nome_duelista' || input.name === 'nome') {
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
        // Ctrl/Cmd + Enter to submit forms
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeForm = document.querySelector('form');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        }
        
        // Escape to go back
        if (e.key === 'Escape') {
            const backBtn = document.querySelector('a[href*="index"], .btn-secondary');
            if (backBtn) {
                backBtn.click();
            }
        }
    });

    // Print functionality
    window.printRanking = function() {
        const printWindow = window.open('', '_blank');
        const rankingTable = document.querySelector('.table');
        
        if (rankingTable) {
            printWindow.document.write(`
                <html>
                <head>
                    <title>Ranking - Liga YGO Marabá</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .header { text-align: center; margin-bottom: 20px; }
                        @media print { .no-print { display: none; } }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Liga YGO Marabá - Ranking dos Duelistas</h2>
                            <p>Gerado em: ${new Date().toLocaleString('pt-BR')}</p>
                        </div>
                        ${rankingTable.outerHTML}
                    </div>
                    <script>window.print(); window.close();</script>
                </body>
                </html>
            `);
            printWindow.document.close();
        }
    };

    // Add print button if on ranking page
    if (window.location.pathname.includes('ranking')) {
        const cardFooter = document.querySelector('.card-footer .btn-group');
        if (cardFooter) {
            const printBtn = document.createElement('button');
            printBtn.className = 'btn btn-outline-success';
            printBtn.innerHTML = '<i class="fas fa-print"></i> Imprimir';
            printBtn.onclick = window.printRanking;
            cardFooter.appendChild(printBtn);
        }
    }

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
    window.YGOUtils = {
        showToast: showToast,
        validateInput: validateInput,
        sortTable: sortTable
    };
});

// Additional utilities
function formatNumber(num) {
    return new Intl.NumberFormat('pt-BR').format(num);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
}