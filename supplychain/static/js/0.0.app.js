// Biến theo dõi người dùng có đang gõ dở dữ liệu không
let hasUnsavedChanges = false;

document.addEventListener("DOMContentLoaded", function () {
    // 1. Sidebar is now included via Django template, no need to fetch
    // Find the active menu item
    let currentPage = window.location.pathname;
    if (currentPage === "/") currentPage = "/tongquan/";  // Default to overview if root

    let links = document.querySelectorAll(".menu-link");
    links.forEach(link => {
        if (link.getAttribute("href") === currentPage) {
            link.classList.add("active");
        }

        // 3. Cảnh báo nếu click menu mà chưa lưu dữ liệu
        link.addEventListener("click", function(event) {
            if (hasUnsavedChanges) {
                let confirmLeave = confirm("⚠️ Bạn có dữ liệu chưa lưu! Bạn có chắc chắn muốn rời khỏi trang này không?");
                if (!confirmLeave) {
                    event.preventDefault(); // Chặn chuyển trang
                }
            }
        });
    });

    // Cảnh báo nút đăng xuất
    const logoutBtn = document.querySelector('.logout-btn');
    if(logoutBtn) {
         logoutBtn.addEventListener("click", function(event) {
            event.preventDefault(); // Luôn ngăn mặc định
            if (hasUnsavedChanges && !confirm("Dữ liệu chưa lưu sẽ bị mất. Vẫn tiếp tục?")) {
                return;
            }
            if (confirm("Bạn có chắc chắn muốn đăng xuất khỏi hệ thống?")) {
                window.location.href = "/dangnhap/";
            }
        });
    }
});

// Hàm gọi khi bắt đầu gõ vào form
function markAsUnsaved() { hasUnsavedChanges = true; }

// Hàm gọi khi đã lưu thành công
function markAsSaved() { hasUnsavedChanges = false; }

// ==========================================
// HÀM HIỂN THỊ MODAL XÓA DÙNG CHUNG CỦA HỆ THỐNG
// ==========================================
function showDeleteModal(entityName, message, onConfirm) {
    let modal = document.getElementById('globalDeleteModal');
    if (!modal) {
        const modalHtml = `
        <div id="globalDeleteModal" class="modal-overlay" style="display: none; align-items: center; justify-content: center; z-index: 10000; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background-color: rgba(0, 0, 0, 0.6);">
            <div class="custom-popup-card" style="max-width: 400px; width: 90%; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.25);">
                <div class="popup-header" style="background-color: #dc3545; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center;">
                    <h5 class="popup-title" id="deleteModalTitle" style="margin: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                        <i class="fas fa-trash-alt"></i> <span>Xóa dữ liệu</span>
                    </h5>
                    <button type="button" class="btn-close-custom" onclick="document.getElementById('globalDeleteModal').style.display='none'" style="background: none; border: none; color: white; cursor: pointer; font-size: 1.2rem;"><i class="fas fa-times"></i></button>
                </div>
                <div class="popup-body" style="padding: 25px 20px; text-align: center;">
                    <p id="deleteModalMessage" style="margin: 0; font-size: 1.05rem; font-weight: 500; color: #333;">Bạn có chắc muốn xóa?</p>
                </div>
                <div class="popup-footer" style="padding: 15px 20px; border-top: 1px solid #eee; display: flex; justify-content: center; gap: 15px; background: #fff;">
                    <button type="button" class="btn-cancel" onclick="document.getElementById('globalDeleteModal').style.display='none'" style="background: #e2e6ea; border: none; padding: 8px 20px; border-radius: 4px; font-weight: 600; cursor: pointer; color: #333;">Hủy bỏ</button>
                    <button type="button" class="btn-save" id="deleteModalConfirmBtn" style="background: #dc3545; color: white; border: none; padding: 8px 20px; border-radius: 4px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                        <i class="fas fa-save"></i> Xác nhận
                    </button>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('globalDeleteModal');
    }

    // Gắn giá trị nội dung
    const titleSpan = document.querySelector('#deleteModalTitle span');
    if (titleSpan) titleSpan.innerText = 'Xóa ' + entityName;
    
    document.getElementById('deleteModalMessage').innerText = message;
    
    // Xử lý sự kiện nút xác nhận
    const confirmBtn = document.getElementById('deleteModalConfirmBtn');
    // Clone node để xoá hết event listener cũ
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    });

    // Hiện modal
    modal.style.display = 'flex';
}

// ==========================================
// PHÂN TRANG ĐÃ TẮT TOÀN HỆ THỐNG (dùng scroll bảng)
// ==========================================
function renderGlobalPagination(totalItems, itemsPerPage, currentPage, containerId, itemName, onPageChangeName) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
}

// ==========================================
// HÀM HIỂN THỊ AUTOCOMPLETE CHO Ô TÌM KIẾM
// ==========================================
function setupSearchAutocomplete(inputId, searchFn, displayFn, selectFn) {
    const input = document.getElementById(inputId);
    if (!input) return;

    if (input.dataset.autocompleteInitialized) return;
    input.dataset.autocompleteInitialized = 'true';

    const container = document.createElement('div');
    container.className = 'search-suggestions';
    input.parentNode.appendChild(container);

    function showSuggestions() {
        const kw = input.value.toLowerCase().trim();
        const results = searchFn(kw).slice(0, 10);
        
        if (results.length === 0) {
            container.innerHTML = '<div class="p-3 text-[13px] text-gray-500 italic text-center">Không tìm thấy kết quả phù hợp</div>';
            container.classList.add('active');
            return;
        }

        container.innerHTML = results.map((item, idx) => `<div class="suggestion-item" data-index="${idx}">${displayFn(item, kw)}</div>`).join('');
        
        container.querySelectorAll('.suggestion-item').forEach(el => {
            el.addEventListener('click', () => {
                const idx = el.getAttribute('data-index');
                selectFn(results[idx], input);
                container.classList.remove('active');
            });
        });

        container.classList.add('active');
    }

    input.addEventListener('input', showSuggestions);
    input.addEventListener('focus', showSuggestions);
    input.addEventListener('click', showSuggestions);

    document.addEventListener('click', (e) => {
        if (!input.parentNode.contains(e.target)) {
            container.classList.remove('active');
        }
    });
    
    input.addEventListener('focus', function() {
        if (this.value.trim() && container.innerHTML !== '') {
            container.classList.add('active');
        }
    });
}