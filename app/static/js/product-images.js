document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = e => {
                const box = this.previousElementSibling;
                box.innerHTML = `
                    <img src="${e.target.result}"
                         style="width:100%; height:100%; object-fit:cover;">
                `;
            };
            reader.readAsDataURL(file);
        });
    });
});

document.addEventListener("DOMContentLoaded", function() {
    const addSection = document.getElementById('categoryAddSection');
    const editSection = document.getElementById('categoryEditSection');
    const deleteSection = document.getElementById('categoryDeleteSection');
    const title = document.getElementById('manageCategoryTitle');

    // All footer buttons with data-action
    const buttons = document.querySelectorAll('#manageCategoryModal .modal-footer button[data-action]');

    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const action = btn.getAttribute('data-action');

            // Hide all sections first
            addSection.style.display = 'none';
            editSection.style.display = 'none';
            deleteSection.style.display = 'none';

            if (action === 'add') {
                addSection.style.display = 'block';
                title.innerText = "Add Category";
            } else if (action === 'edit') {
                editSection.style.display = 'block';
                title.innerText = "Edit Category";
            } else if (action === 'delete') {
                deleteSection.style.display = 'block';
                title.innerText = "Delete Category";
            }
        });
    });
});
