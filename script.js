// --- 1. HIỆU ỨNG HIỆN CHỮ KHI CUỘN TRANG ---
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add('show');
        }
    });
}, {
    rootMargin: "0px 0px -30px 0px",
    threshold: 0.01
});

const hiddenElements = document.querySelectorAll('.hidden');
hiddenElements.forEach((el) => observer.observe(el));


// --- 2. ĐIỀU KHIỂN PHÁT NHẠC ---
const musicBtn = document.getElementById('musicBtn');
const lofiTrack = document.getElementById('lofiTrack');

musicBtn.addEventListener('click', () => {
    if (lofiTrack.paused) {
        lofiTrack.play();
        musicBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Tắt Nhạc';
    } else {
        lofiTrack.pause();
        musicBtn.innerHTML = '<i class="fa-solid fa-music"></i> Bật Nhạc Lofi';
    }
});


// --- 3. HIỆU ỨNG HẠT VÀNG NẮNG RƠI NHẸ ---
const canvas = document.getElementById('snow');
const ctx = canvas.getContext('2d');

let width = canvas.width = window.innerWidth;
let height = canvas.height = window.innerHeight;

window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
});

const numFlakes = 40;
const flakes = [];

for (let i = 0; i < numFlakes; i++) {
    flakes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        r: Math.random() * 2 + 0.5,
        d: Math.random() * numFlakes,
        speed: Math.random() * 0.4 + 0.2
    });
}

function drawSnow() {
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = 'rgba(212, 163, 115, 0.18)';
    ctx.beginPath();
    
    for (let i = 0; i < numFlakes; i++) {
        const f = flakes[i];
        ctx.moveTo(f.x, f.y);
        ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2, true);
        
        f.y += f.speed;
        f.x += Math.sin(f.d) * 0.2;
        f.d += 0.005;

        if (f.y > height) {
            flakes[i] = { x: Math.random() * width, y: 0, r: f.r, d: f.d, speed: f.speed };
        }
    }
    ctx.fill();
    requestAnimationFrame(drawSnow);
}

drawSnow();


// --- 4. XỬ LÝ HỘP THƯ GỬI LỜI NHẮN (MỚI TĂNG TƯƠNG TÁC) ---
const sendBtn = document.getElementById('sendBtn');
const userMsg = document.getElementById('userMsg');

if (sendBtn && userMsg) {
    sendBtn.addEventListener('click', () => {
        const text = userMsg.value.trim();
        if (text === "") {
            alert("Bạn chưa nhập lời nhắn nào kìa! 🌸");
        } else {
            alert(`Cảm ơn bạn đã gửi lời nhắn: "${text}". Mình đã nhận được rồi nhé! 🥰`);
            userMsg.value = ""; // Xóa nội dung khung nhập sau khi gửi thành công
        }
    });
}

// Ảnh đại diện dự phòng
const avatarImg = document.querySelector('.avatar-img');
if (avatarImg) {
    avatarImg.addEventListener('error', function() {
        this.src = 'https://imgur.com';
    });
}
