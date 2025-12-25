document.addEventListener("DOMContentLoaded", function () {
    // =========================
    // Image Preview (Profile & Product)
    // =========================
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            // Use the first div inside the label as preview container
            let box = this.closest('label').querySelector('div');
            if (!box) return;

            const reader = new FileReader();
            reader.onload = e => {
                box.innerHTML = `<img src="${e.target.result}" 
                                     style="width:100%; height:100%; object-fit:cover;">`;
            };
            reader.readAsDataURL(file);
        });
    });

    // =========================
    // Category Modal Sections
    // =========================
    const addSection = document.getElementById('categoryAddSection');
    const editSection = document.getElementById('categoryEditSection');
    const deleteSection = document.getElementById('categoryDeleteSection');
    const title = document.getElementById('manageCategoryTitle');
    const buttons = document.querySelectorAll('#manageCategoryModal .modal-footer button[data-action]');

    if (buttons) {
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.getAttribute('data-action');

                // Hide all sections first
                if (addSection) addSection.style.display = 'none';
                if (editSection) editSection.style.display = 'none';
                if (deleteSection) deleteSection.style.display = 'none';

                // Show the chosen section
                if (action === 'add' && addSection) {
                    addSection.style.display = 'block';
                    if (title) title.innerText = "Add Category";
                } else if (action === 'edit' && editSection) {
                    editSection.style.display = 'block';
                    if (title) title.innerText = "Edit Category";
                } else if (action === 'delete' && deleteSection) {
                    deleteSection.style.display = 'block';
                    if (title) title.innerText = "Delete Category";
                }
            });
        });
    }
});


function comingSoon(e) {
    e.preventDefault(); // prevent actual link navigation
    alert("Coming soon 🚀");
}
